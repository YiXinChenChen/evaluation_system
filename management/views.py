# -*-coding:utf-8-*-
import json
import logging
import os
import uuid

from django import forms
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse, JsonResponse, HttpResponseNotAllowed, HttpResponseBadRequest
from django.shortcuts import render
from django.shortcuts import render_to_response
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from core.models import App
from core.models import Case
from core.models import CaseGroup
from core.models import CaseTestObj
from core.models import Execution
from core.models import Scene
from core.models import Suite
from core.models import TestObj

from forms import SuiteStartForm

logger = logging.getLogger(__name__)


def _delete_case_func(case_id):
    case_testobjs = CaseTestObj.objects.filter(case_id=case_id)
    try:
        for case_testobj in case_testobjs:
            try:
                testobj_count = CaseTestObj.objects.filter(
                    testobj_id=case_testobj.testobj_id).count()
                if (testobj_count == 1):
                    testobj = TestObj.objects.get(pk=case_testobj.testobj_id,
                                                  is_locked=1)
                    testobj.is_locked = 0
                    testobj.save()
            except Exception, e:
                logger.exception(e.message)
            case_testobj.delete()
        case = Case.objects.get(pk=case_id)
        case.delete()
    except Exception, e:
        logger.exception(e.message)


def _get_suite_status(suite_id):
    try:
        return Suite.objects.get(pk=suite_id).status
    except Exception, e:
        logger.warning('suite does not exist')
        logger.exception(e.message)
        return None


def __check_suite_status(suite_id):
    status = _get_suite_status(suite_id)
    if status:
        if status == 'testing':
            pass
            # TODO error page
            # return HttpResponse(
            #     json.dumps({'code': 1, 'msg': 'suite  is in  testing'}))
    else:
        logger.warning('suite does not exist')
        # TODO error page
        # return HttpResponse(
        #     json.dumps({'code': 2, 'msg': 'suite does not exist'}))


def suite_index(request):
    try:
        suite_name = request.GET.get('suiteName', None)
        paginator = {
            'pageNo': int(request.GET.get('page_no', 1)),
            'pageSize': int(request.GET.get('page_size', 20))
        }
    except Exception, e:
        logger.exception(e.message)
        # todo add error page
        return

    logger.info(
        '[Request] suite_name : %s, paginator: %s' % (suite_name, paginator))

    if paginator['pageSize'] < 20:
        paginator['pageSize'] = 20
        logger.info('pageSize less than 20, set it to 20')
    if paginator['pageSize'] > 50:
        paginator['pageSize'] = 50
        logger.info('pageSize more than 50, set it to 50')

    if suite_name is None:
        suite_name = ""
        logger.info("suite_name key word is None,set it ''")

    logger.info(
        '[Actual] filePath: %s, paginator: %s' % (suite_name, paginator))

    offset = (paginator['pageNo'] - 1) * paginator['pageSize']
    try:
        suites = Suite.objects.filter(name__contains=suite_name).order_by(
            "-id")[
                 offset: offset + paginator['pageSize']]
        paginator['totalCounts'] = Suite.objects.filter(
            name__contains=suite_name).count()
    except Exception, e:
        logging.exception(e.message)
        # todo add error page
        return

    logger.debug(paginator)

    data = {'suites': suites, 'suite_name': suite_name,
            'paginator': paginator, 'page_type': 'suite_index_page'}

    logger.info('[Response] data: %s}' % (data,))

    # return render_to_response('management/suiteIndex.html', data)
    return render(request, 'management/suiteIndex.html', data)


@csrf_exempt
def scene_edit_add(request):
    try:
        scene_id = request.POST.get('scene_id', '')
        scene_name = request.POST.get('scene_name', '')
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(json.dump({'code': 0, 'msg': 'get params exception'}))

    if scene_id < 0:
        logger.warning('app_id is invalid')
        return HttpResponse(json.dumps({'code': 7, 'msg': 'app_id is invalid'}))
    if scene_name == '':
        logger.warning("the scene name is empty")
        return HttpResponse(json.dumps({'code': 5, 'msg': 'the scene name is empty'}))

    if scene_id == '':  # 添加
        if Scene.objects.filter(name=scene_name).count() > 0:
            return HttpResponse(json.dumps({'code': 3, 'msg': 'scene_name is exist'}))

        try:
            scenes = Scene()
            scenes.name = scene_name
            scenes.save()
            return HttpResponse(json.dumps({'code': 0, 'msg': 'OK'}))
        except Exception, e:
            logger.exception(e.message)
            return HttpResponse(json.dumps({'code': 4, 'msg': 'create scene error'}))


    else:  # 编辑
        scenes = Scene.objects.get(id=scene_id)
        if Scene.objects.filter(name=scene_name).count() > 0 and scenes.name != scene_name:
            return HttpResponse(json.dumps({'code': 3, 'msg': 'scene_name is exist'}))
        try:
            scenes.name = scene_name
            scenes.save()
            return HttpResponse(json.dumps({'code': 0, 'msg': 'OK'}))
        except Exception, e:
            logger.exception(e.message)
            return HttpResponse(json.dumps({'code': 6, 'msg': 'edit scene error'}))


def add_suite_handler(request):
    try:
        suite_name = request.GET.get('suiteName', '')
        split_type = request.GET.get('splitType', '')
        case_count = request.GET.get('caseCount', '0')
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 1, 'msg': 'get request params error'}))

    logger.info('[Request] suiteName: %s, splitType: %s, caseCount :%s' % (
        suite_name, split_type, case_count))

    if suite_name == '':
        logger.error('suiteName value error')
        return HttpResponse(
            json.dumps({'code': 2, 'msg': 'suiteName value error '}))

    legal_split_type = ['manually', 'auto']

    if split_type not in legal_split_type:
        logger.error('split type error')
        return HttpResponse(
            json.dumps({'code': 3, 'msg': 'splitType value error'}))

    try:
        case_count_int = int(case_count)
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 4, 'msg': 'caseObjCount parse int error'}))

    if case_count_int < 2 or case_count_int > 4:
        logger.error('caseObjCount value error')
        return HttpResponse(
            json.dumps({'code': 5, 'msg': 'caseObjCount value error'}))

    suite = Suite()
    suite.name = suite_name
    suite.uuid = str(uuid.uuid4())
    suite.split_type = split_type
    suite.case_obj_count = case_count_int
    suite.status = 'ready'
    suite.save()

    logger.info('add suite success')

    return HttpResponse(json.dumps({'code': 0, 'msg': 'add suite success'}))


def start_suite_handler(request):
    if not request.method == 'POST':
        return HttpResponseNotAllowed()

    form = SuiteStartForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'code': 1, 'msg': 'get request params error', 'errors': form.errors.as_json()})

    # try:
    #     suite_id = request.POST.get('suite_id', '')
    #     start_date = request.POST.get('start_date', None)
    #     end_date = request.POST.get('end_date', None)
    #     case_count = request.POST.get('case_count', None)
    # except Exception, e:
    #     logger.exception(e.message)
    #     return HttpResponse(json.dumps({'code': 1, 'msg': 'get request params error'}))
    #
    # if start_date is None or end_date is None:
    #     return JsonResponse({'code': 2, 'msg': 'get request params error'})
    #
    # if case_count is not None:
    #     try:
    #         case_count = int(case_count)
    #     except (ValueError, TypeError):
    #         case_count = None

    suite_id = form.cleaned_data['suite_id']
    start_date = form.cleaned_data['start_date']
    end_date = form.cleaned_data['end_date']
    case_count = form.cleaned_data['case_count']

    logger.info('[Request]suite_id:%d', suite_id)

    suite = None
    groups = None
    cases = None
    case_testobjs = None

    try:
        suite = Suite.objects.get(id=suite_id)
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 3, 'msg': 'get target suite exception'}))

    if suite.status != 'ready':
        logger.warning('suite status is %s', (suite.status))
        return HttpResponse(json.dumps(
            {'code': 4, 'msg': 'suite status is {0}'.format(suite.status)}))

    try:
        groups = CaseGroup.objects.filter(suite_id=suite_id)
        if groups.count() is 0:
            return HttpResponse(json.dumps(
                {'code': 5, 'msg': 'suite has no group'}))

        for group in groups:
            cases = Case.objects.filter(group_id=group.id)
            if len(cases) is 0:
                return HttpResponse(json.dumps(
                    {'code': 6, 'msg': 'group %s has no cases' % group.id}))

            if case_count is None:
                case_count = len(cases)
                logger.debug('[start_suite_handler] set suite id=%d case_count=%d' % (suite.id, case_count))

            for case in cases:
                case_testobjs = CaseTestObj.objects.filter(case_id=case.id)
                if case_testobjs.count() != suite.case_obj_count:
                    return HttpResponse(json.dumps(
                        {'code': 7, 'msg': 'testobj number need equal to '
                                           'suite case_obj_count'}))
    except Exception, e:
        logger.exception(e.message)
        return JsonResponse({'code': 8, 'msg': e.message})

    # suite.status = 'testing'
    # suite.start_date = start_date
    # suite.end_date = end_date
    # suite.case_count = case_count
    try:
        # suite.save()
        update_count = Suite.objects.filter(id=suite.id, status='ready').update(status='testing', start_date=start_date, end_date=end_date, case_count=case_count)
        if update_count == 0:
            return JsonResponse({'code': 9, 'msg': 'suite id=%d update failed' % (suite.id,)})
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 10, 'msg': 'update target suite exception'}))

    return HttpResponse(json.dumps({'code': 0, 'msg': 'update success'}))


@csrf_exempt
def finish_suite_handler(request):
    try:
        suite_id = request.POST.get('suite_id', '')
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 1, 'msg': 'get request params error'}))

    logger.info('[Request]suite_id:%s', (suite_id))
    transaction.set_autocommit(False)

    try:
        Suite.objects.filter(id=suite_id, status='testing').update(status='invalid')
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 2, 'msg': 'get target suite exception'}))

    # 检查execution的状态并进行修改状态
    try:
        Execution.objects.filter(suite_id=suite_id, status='ready').update(status='finished')
        transaction.commit()
    except Exception, e:
        transaction.rollback()
        logger.exception(e.message)
        return HttpResponse(json.dumps({'code': 3, 'msg': 'get execution exception'}))

    return HttpResponse(json.dumps({'code': 0, 'msg': 'update success'}))


@csrf_exempt
def edit_suite_handler(request):
    try:
        suite_id = request.POST.get('suite_id', '')
        suite_name = request.POST.get('suite_name', '')
        split_type = request.POST.get('split_type', '')
        case_obj_count = request.POST.get('case_count', '')
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 1, 'msg': 'get request params error'}))

    logger.info(
        '[Request]suite_Id:%s, suite_name:%s, split_type:%s,case_obj_count:%s',
        (suite_id, suite_name, split_type, case_obj_count))
    if suite_id == '':
        logger.warning('suite_id values error')
        return HttpResponse(
            json.dumps({'code': 2, 'msg': 'suite_id value error'}))
    if suite_name == '':
        logger.warning('suite_id values error')
        return HttpResponse(
            json.dumps({'code': 3, 'msg': 'suite_name value error'}))
    if split_type == '':
        logger.warning('suite_id values error')
        return HttpResponse(
            json.dumps({'code': 4, 'msg': 'split_type value error'}))
    if case_obj_count == '':
        logger.warning('suite_id values error')
        return HttpResponse(
            json.dumps({'code': 5, 'msg': 'case_obj_count value error'}))

    try:
        Suite.objects.filter(id=suite_id, status='ready').update(name=suite_name, split_type=split_type,
                                                                 case_obj_count=case_obj_count)
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 6, 'msg': 'update suite exception'}))

    return HttpResponse(json.dumps({'code': 0, 'msg': 'edit success'}))


def suite_group_index(request):
    try:
        suite_id = request.GET.get('suite_id', None)
        group_name = request.GET.get('group_name', '')
        paginator = {
            'pageNo': int(request.GET.get('page_no', 1)),
            'pageSize': int(request.GET.get('page_size', 20))
        }
    except Exception, e:
        logger.exception(e.message)
        # todo add error page
        return

    logger.info(
        '[Request] suite_id : %s, paginator: %s' % (suite_id, paginator))

    if paginator['pageSize'] < 20:
        paginator['pageSize'] = 20
        logger.info('pageSize less than 20, set it to 20')
    if paginator['pageSize'] > 50:
        paginator['pageSize'] = 50
        logger.info('pageSize more than 50, set it to 50')

    if suite_id is None:
        logger.warning('suiteID is None')
        # TODO error page
        return

    logger.info(
        '[Actual] suiteId: %s, paginator: %s' % (suite_id, paginator))

    offset = (paginator['pageNo'] - 1) * paginator['pageSize']
    try:
        groups = CaseGroup.objects.filter(suite_id=suite_id,
                                          name__contains=group_name).order_by(
            "-id")[
                 offset: offset + paginator['pageSize']]
        paginator['totalCounts'] = groups.count()
        cases = Case.objects.filter(suite_id=suite_id).order_by('-id')
    except Exception, e:
        logging.exception(e.message)
        # todo add error page
        return

    logger.debug(paginator)

    disable_cud = 'false'

    if (_get_suite_status(suite_id) == 'testing'):
        disable_cud = 'true'

    data = {'suite_id': suite_id, 'paginator': paginator, 'disable_cud': disable_cud,
            'page_type': 'suite_index_page', 'groups': groups,
            'cases': cases, 'group_name': group_name}

    logger.info('[Response] data: %s}' % (data,))

    return render_to_response('management/addSuiteGroup.html', data)


@csrf_exempt
def add_suite_group(request):
    try:
        group_name = request.POST.get('group_name', '')
        suite_id = request.POST.get('suite_id', '')
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 1, 'msg': 'get group_name or suite_id error'}))

    logger.info('[Request] groupName: %s, suiteId: %s' % (group_name, suite_id))

    if group_name == '':
        logger.warning('groupName value is None')
        return HttpResponse(
            json.dumps({'code': 2, 'msg': 'groupName value is None '}))

    if suite_id == '':
        logger.warning('suiteId value is None')
        return HttpResponse(
            json.dumps({'code': 2, 'msg': 'suiteId value is None '}))

    try:
        suite_id = int(suite_id)
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 3, 'msg': 'suiteId  is not number '}))

    __check_suite_status(suite_id)

    group = CaseGroup()
    group.name = group_name
    group.suite_id = suite_id
    group.save()

    logger.info('add suite success')

    return HttpResponse(json.dumps({'code': 0, 'msg': 'add group  success'}))


def scene_index(request):
    try:
        scene_name = request.GET.get('scene_name', '')
        paginator = {
            'pageNo': int(request.GET.get('page_no', 1)),
            'pageSize': int(request.GET.get('page_size', 20))
        }
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 1, 'msg': 'get request params error'}))

    logger.info(
        '[Request] scene_name: %s, paginator: %s' % (scene_name, paginator,))

    if paginator['pageSize'] < 20:
        paginator['pageSize'] = 20
        logger.info('pageSize less than 20, set it to 20')
    if paginator['pageSize'] > 50:
        paginator['pageSize'] = 50
        logger.info('pageSize more than 50, set it to 50')

    logger.info(
        '[Actual] scene_name: %s, paginator: %s' % (scene_name, paginator,))

    offset = (paginator['pageNo'] - 1) * paginator['pageSize']
    try:
        scenes = Scene.objects.filter(name__contains=scene_name).order_by(
            "-id")[
                 offset: offset + paginator['pageSize']]
        paginator['totalCounts'] = Scene.objects.filter(
            name__contains=scene_name).count()
    except Exception, e:
        logging.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 2, 'msg': 'get scenes list error'}))

    data = {'scenes': scenes, 'paginator': paginator,
            'page_type': 'scene_index_page'}
    return render_to_response('management/sceneIndex.html', data)


def app_index(request):
    try:
        paginator = {
            'pageNo': int(request.GET.get('page_no', 1)),
            'pageSize': int(request.GET.get('page_size', 20))
        }
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 1, 'msg': 'get request params error'}))

    logger.info('[Request] paginator: %s' % (paginator,))

    if paginator['pageSize'] < 20:
        paginator['pageSize'] = 20
        logger.info('pageSize less than 20, set it to 20')
    if paginator['pageSize'] > 50:
        paginator['pageSize'] = 50
        logger.info('pageSize more than 50, set it to 50')

    logger.info('[Actual] paginator: %s' % (paginator,))

    offset = (paginator['pageNo'] - 1) * paginator['pageSize']
    try:
        apps = App.objects.all().order_by("-id")[
               offset: offset + paginator['pageSize']]
        paginator['totalCounts'] = App.objects.all().count()
    except Exception, e:
        logging.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 2, 'msg': 'get apps list error'}))

    data = {'apps': apps, 'paginator': paginator, 'page_type': 'app_index_page'}
    logger.info('[Response] data: %s}' % (data,))
    return render_to_response('management/appIndex.html', data)


@csrf_exempt
def add_app_handler(request):
    try:
        app_name = request.POST.get('app_name', '')
        app_display_name = request.POST.get('app_display_name', '')
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 1, 'msg': 'get request params error'}))

    logger.info('[Request] app_name: %s app_display_name %s' % (
        app_name, app_display_name,))

    if app_name == '':
        logger.warning('app_name is empty')
        return HttpResponse(json.dumps({'code': 2, 'msg': 'app_name is empty'}))
    if app_display_name == '':
        logger.warning('app_display_name is empty')
        return HttpResponse(
            json.dumps({'code': 3, 'msg': 'app_display_name is empty'}))

    try:
        if App.objects.filter(name=app_name).count() > 0:
            return HttpResponse(
                json.dumps({'code': 4, 'msg': 'app_name is exist'}))
    except Exception, e:
        logger.error(e.message)
        return HttpResponse(
            json.dumps({'code': 5, 'msg': 'app_name verification fails'}))

    try:
        app = App()
        app.name = app_name
        app.display_name = app_display_name
        app.status = 'created'
        app.save()
    except Exception, e:
        logger.error(e.message)
        return HttpResponse(json.dumps({'code': 6, 'msg': 'create app error'}))

    return HttpResponse(json.dumps({'code': 0, 'msg': 'success'}))


@csrf_exempt
def edit_app_handler(request):
    try:
        app_id = int(request.POST.get('app_id', -1))
        app_name = request.POST.get('app_name', '')
        app_display_name = request.POST.get('app_display_name', '')
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 1, 'msg': 'get request params error'}))

    logger.info('[Request] app_id: %s app_name: %s app_display_name: %s' % (
        app_id, app_name, app_display_name,))

    if app_id < 0:
        logger.warning('app_id is invalid')
        return HttpResponse(json.dumps({'code': 2, 'msg': 'app_id is invalid'}))
    if app_name == '':
        logger.warning('app_name is empty')
        return HttpResponse(json.dumps({'code': 3, 'msg': 'app_name is empty'}))
    if app_display_name == '':
        logger.warning('app_display_name is empty')
        return HttpResponse(
            json.dumps({'code': 4, 'msg': 'app_display_name is empty'}))

    app = App.objects.get(id=app_id)

    try:
        if App.objects.filter(
                name=app_name).count() > 0 and app_name != app.name:
            return HttpResponse(
                json.dumps({'code': 5, 'msg': 'app_name is exist'}))
    except Exception, e:
        logger.error(e.message)
        return HttpResponse(
            json.dumps({'code': 6, 'msg': 'app_name verification fails'}))

    try:
        app.name = app_name
        app.display_name = app_display_name
        app.save()
    except Exception, e:
        logger.error(e.message)
        return HttpResponse(json.dumps({'code': 6, 'msg': 'update app error'}))

    return HttpResponse(json.dumps({'code': 0, 'msg': 'success'}))


@csrf_exempt
def delete_app_handler(request):
    try:
        app_id = int(request.POST.get('app_id', -1))
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 1, 'msg': 'get request params error'}))

    logger.info('[Request] app_id: %s' % (app_id,))

    try:
        App.objects.filter(id=app_id).delete()
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(json.dumps({'code': 2, 'msg': 'delete app error'}))

    return HttpResponse(json.dumps({'code': 0, 'msg': 'success'}))


@csrf_exempt
def edit_group(request):
    try:
        group_id = request.POST.get('group_id', '')
        group_name = request.POST.get('group_name', '')
        suite_id = request.POST.get('suite_id', -1)
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 1, 'msg': 'get request params error'}))

    logger.info(
        '[Request] group_id: %s, group_name: %s' % (group_id, group_name))

    try:
        suite_id = int(suite_id)
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 2, 'msg': 'suiteId  is not number '}))

    __check_suite_status(suite_id)

    if group_id == '':
        logger.warning('group_id is null')
        return HttpResponse(
            json.dumps({'code': 2, 'msg': 'group_id is null'}))

    if group_name == '':
        logger.warning('group_name is null')
        return HttpResponse(
            json.dumps({'code': 2, 'msg': 'group_name is null'}))

    group = CaseGroup.objects.get(id=group_id)

    if group:
        group.name = group_name
        group.mtime = timezone.now()
        group.save()
        logger.info('edit group success')
        return HttpResponse(json.dumps({'code': 0, 'msg': "edit group "
                                                          "success"}))
    else:
        logger.warning("group does'nt exist")
        return HttpResponse(
            json.dumps({'code': 3, 'msg': "group does'nt exist"}))


@csrf_exempt
def delete_group(request):
    try:
        group_id = request.POST.get('group_id', '')
        suite_id = request.GET.get('suite_id', -1)
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 1, 'msg': 'get group_id error'}))

    logger.info(
        '[Request] group_id: %s' % group_id)

    __check_suite_status(suite_id)

    if group_id == '':
        logger.warning('group_id is null')
        return HttpResponse(
            json.dumps({'code': 2, 'msg': 'group_id is null'}))

    try:
        suite = Suite.objects.filter(id=suite_id).filter(
            status='testing')
        if suite:
            return HttpResponse(
                json.dumps({'code': 3, 'msg': 'suite is in testing, can not '
                                              'delete'}))
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 2, 'msg': 'get target suite exception'}))

    group = CaseGroup.objects.get(id=group_id)

    if group is not None:
        group.delete()
        logger.info('delete group %s success' % group_id)

        try:
            cases = Case.objects.filter(group_id=group_id)
            for case in cases:
                _delete_case_func(case.id)
        except Exception, e:
            logger.exception(e.message)

        return HttpResponse(json.dumps({'code': 0, 'msg': "delete group "
                                                          "success"}))
    else:
        logger.warning("group does'nt exist")
        return HttpResponse(
            json.dumps({'code': 1, 'msg': "group does'nt exist"}))


def add_case_index(request):
    from django.db import connection
    try:
        is_edit = request.GET.get('is_edit', 'false')
        case_id = request.GET.get('case_id', '')
        suite_id = request.GET.get('suite_id', '')
        group_id = request.GET.get('group_id', '')
        app_name = request.GET.get('app_name', '')
        scene_name = request.GET.get('scene_name', '')
        tag_val = request.GET.get('tag_val', '')
        file_path = request.GET.get('file_path', '')
        paginator = {
            'pageNo': int(request.GET.get('page_no', 1)),
            'pageSize': int(request.GET.get('page_size', 20))
        }
    except Exception, e:
        logger.exception(e.message)
        return

    logger.info(
        '[Request] suite_id: %s paginator:%s, app_name:%s, scene_name:%s,tag_val:%s, file_path:%s',
        (suite_id, paginator, app_name, scene_name, tag_val, file_path))

    if paginator['pageSize'] < 20:
        paginator['pageSize'] = 20
        logger.info('pageSize less than 20, set it to 20')
    if paginator['pageSize'] > 50:
        paginator['pageSize'] = 50
        logger.info('pageSize more than 50, set it to 50')

    app_name_sql = "'%" + app_name + "%'"
    scene_name_sql = "'%" + scene_name + "%'"
    tag_val_sql = "'%" + tag_val + "%'"
    file_path_sql = "'%" + file_path + "%'"

    search_added = 'SELECT ' \
                   'test_objs.id,' \
                   'apps.`name`,' \
                   'scenes.`name`,' \
                   'test_objs.type,' \
                   'test_objs.tag,' \
                   'test_objs.path,' \
                   'test_objs.ctime,' \
                   'case_testobjs.id,'\
                   'case_testobjs.order '\
                   'FROM ' \
                   'case_testobjs ' \
                   'INNER JOIN test_objs ON case_testobjs.testobj_id = test_objs.id ' \
                   'INNER JOIN apps ON test_objs.app_id = apps.id ' \
                   'INNER JOIN scenes ON test_objs.scene_id = scenes.id ' \
                   'WHERE ' \
                   'case_testobjs.case_id LIKE ' + case_id + ' ' \
                   'ORDER BY  case_testobjs.order '

    # cursor = None
    # try:
    #     cursor = connection.cursor()
    #     # ...
    # # expect:
    # finally:
    #     if cursor is not None:
    #         cursor.close()

    cursor = connection.cursor()
    cursor.execute(search_added)
    added_testobjs_records = cursor.fetchall()
    cursor.close()

    added_testobjs = []
    for (id, app, scene, type, tag, path, ctime, c_o_id, order) in added_testobjs_records:
        added = {'id': id, 'app': app, 'scene': scene, 'type': type,
                 'tag': tag, 'path': path, 'ctime': ctime, 'c_o_id': c_o_id, 'order': order}
        added_testobjs.append(added)

    id_list = []
    for item in added_testobjs:
        id_list.append(int(item['id']))
    id_list = tuple(id_list)
    id_str = id_list.__str__()

    if id_str[len(id_str) - 2] == ',':
        id_str = id_str[: len(id_str) - 2] + ')'
    logger.debug(id_str)

    if len(id_str) == 2:
        id_str = '(-1)'

    offset = (paginator['pageNo'] - 1) * paginator['pageSize']

    search_none_added = 'SELECT ' \
                        'test_objs.id,' \
                        'apps.`name`,' \
                        'scenes.`name`,' \
                        'test_objs.type,' \
                        'test_objs.tag,' \
                        'test_objs.path,' \
                        'test_objs.ctime ' \
                        'FROM ' \
                        'test_objs ' \
                        'INNER JOIN apps ON test_objs.app_id = apps.id ' \
                        'INNER JOIN scenes ON test_objs.scene_id = scenes.id ' \
                        'WHERE apps.name LIKE ' + app_name_sql + ' AND ' \
                                                                 'scenes.name LIKE ' + scene_name_sql + ' AND ' \
                                                                                                        'test_objs.tag LIKE ' + tag_val_sql + ' AND ' \
                                                                                                                                              'test_objs.path LIKE ' + file_path_sql + ' AND ' \
                                                                                                                                                                                       'test_objs.id NOT IN ' + id_str + ' ' \
                                                                                                                                                                                                                         'ORDER BY test_objs.id DESC '
    # 'LIMIT ' + str(offset) + ', ' + str(offset + paginator['pageSize'])

    cursor = connection.cursor()
    cursor.execute(search_none_added)
    none_added = cursor.fetchall()
    cursor.close()

    none_added_objs = []
    for (id, app, scene, type, tag, path, ctime) in none_added:
        none_added_obj = {'id': id, 'app': app, 'scene': scene, 'type': type,
                          'tag': tag, 'path': path, 'ctime': ctime}
        none_added_objs.append(none_added_obj)

    paginator['totalCounts'] = len(none_added_objs)

    none_added_objs = none_added_objs[offset: offset + paginator['pageSize']]

    disable_cud = 'false'

    if (_get_suite_status(suite_id) == 'testing'):
        disable_cud = 'true'

    scenes = Scene.objects.all()
    apps = App.objects.all()

    data = {'case_id': case_id, 'suite_id': suite_id, 'group_id': group_id,
            'app_name': app_name, 'scene_name': scene_name, 'tag_val':
                tag_val, 'file_path': file_path, 'added_objs':
                added_testobjs, 'none_added_objs': none_added_objs, 'paginator':
                paginator, 'page_type': 'suite_index_page', 'is_edit':
                is_edit, 'disable_cud': disable_cud, 'apps': apps, 'scenes':
                scenes}
    return render_to_response('management/addCase.html', data)


@csrf_exempt
def add_case_handler(request):
    try:
        suite_id = request.POST.get('suite_id', '')
        group_id = request.POST.get('group_id', '')
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 1, 'msg': 'get request params error'}))

    logger.info('[Request] suite_id: %s, group_id %s' % (suite_id, group_id))

    if suite_id == '':
        logger.warning('suite_id is empty')
        return HttpResponse(json.dumps({'code': 2, 'msg': 'suite_id is empty'}))
    if group_id == '':
        logger.warning('group_id is empty')
        return HttpResponse(
            json.dumps({'code': 3, 'msg': 'group_id is empty'}))

    try:
        suite_id = int(suite_id)
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 4, 'msg': 'suite_id is not int'}))

    __check_suite_status(suite_id)

    try:
        group_id = int(group_id)
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 5, 'msg': 'group_id is not int'}))
    try:
        case = Case()
        case.suite_id = suite_id
        case.group_id = group_id
        case.save()
        logger.info('add case success')
        return HttpResponse(
            json.dumps({'code': 0, 'msg': 'add case_test_obj success',
                        'case_id': case.id, 'suite_id': suite_id}))
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 6, 'msg': 'add case error'}))


@csrf_exempt
def delete_case_handler(request):
    try:
        suite_id = request.POST.get('suite_id', -1)
        case_id = request.POST.get('case_id', -1)
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 1, 'msg': 'get request params error'}))

    try:
        suite_id = int(suite_id)
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 2, 'msg': 'suite_id is not  int'}))

    try:
        suite = Suite.objects.get(pk=suite_id)
        if suite.status == 'testing':
            return HttpResponse(
                json.dumps({'code': 2, 'msg': 'suite is in testing,  can not '
                                              'delete'}))
    except Exception, e:
        logger.exception(e.message)

    try:
        case_id = int(case_id)
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 1, 'msg': 'case_id is not  int'}))

    _delete_case_func(case_id)

    return HttpResponse(json.dumps({'code': 0, 'msg': 'delete case success',
                                    'suite_id': suite_id}))


@csrf_exempt
def add_case_testobj_handler(request):
    try:
        case_id = request.POST.get('case_id', 0)
        testobj_id = request.POST.get('testobj_id', 0)
        suite_id = request.POST.get('suite_id', 0)
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 1, 'msg': 'get request params error'}))

    logger.info('[Request] case_id: %s, testobj_id: %s' % (case_id, testobj_id))

    if case_id <= 0:
        logger.warning('case_id is empty')
        return HttpResponse(
            json.dumps({'code': 3, 'msg': 'case_id is empty'}))
    if testobj_id <= 0:
        logger.warning('test_obj_id is empty')
        return HttpResponse(
            json.dumps({'code': 3, 'msg': 'test_obj_id is empty'}))
    if suite_id <= 0:
        logger.warning('suite_id is empty')
        return HttpResponse(
            json.dumps({'code': 3, 'msg': 'suite_id is empty'}))

    __check_suite_status(suite_id)

    transaction.set_autocommit(False)

    try:
        number_limit = Suite.objects.get(pk=suite_id).case_obj_count
        now_count = CaseTestObj.objects.filter(case_id=case_id).count()
        if now_count >= number_limit:
            return HttpResponse(
                json.dumps(
                    {'code': 5, 'msg': 'Over number limit, can not add'}))

        now_case_obj = CaseTestObj.objects.filter(case_id=case_id).order_by("-id")[:1]

        if len(now_case_obj)==0:
            now_order = 1
        else:
            now_order = now_case_obj[0].order + 1

        case_test_obj = CaseTestObj()
        case_test_obj.case_id = case_id
        case_test_obj.testobj_id = testobj_id
        case_test_obj.order = now_order
        case_test_obj.save()


        test_obj = TestObj.objects.get(pk=testobj_id)
        if test_obj.is_locked == 0:
            test_obj.is_locked = 1
            test_obj.save()
        transaction.commit()
    except Exception, e:
        print e
        transaction.rollback()
        logger.error(e.message)
        return HttpResponse(json.dumps({'code': 6, 'msg': 'add case_test_obj '
                                                          'error'}))

    return HttpResponse(json.dumps({'code': 0, 'msg': 'add '
                                                      'case_test_obj success'}))
@csrf_exempt
def case_testObj_get_order(request):
    case_id = request.POST.get('case_id', '')
    testobj_id = request.POST.get('testobj_id', '')

    if case_id==''or testobj_id=='':
         return HttpResponse(json.dumps({'code': 1, 'msg': 'get parme error'}))
    try:
        case_testObj = CaseTestObj.objects.get(case_id=case_id, testobj_id=testobj_id)
    except:
        return HttpResponse(json.dumps({'code': 2, 'msg': 'the case_testObj is not exits '}))

    return HttpResponse(json.dumps({'code': 0, 'id':case_testObj.id ,'order': case_testObj.order}))

@csrf_exempt
def case_testObj_sub_order(request):
    case_id = request.POST.get('case_obj_id', '')
    order = request.POST.get('order', '')


    if case_id == '' or order == '':
         return HttpResponse(json.dumps({'code': 1, 'msg': 'the parm is empty'}))

    try:
        case_obj = CaseTestObj.objects.get(id=case_id)
        case_obj.order=order
        case_obj.save()
        return HttpResponse(json.dumps({'code': 0, 'msg': 'success'}))
    except:
        return HttpResponse(json.dumps({'code': 1, 'msg': 'order change fail'}))

def _list_test_objs_by_case_id(case_id):
    from django.db import connection
    list_test_objs_sql = 'SELECT ' \
                        'c.case_id AS case_id, t.id AS test_obj_id, t.type AS type, t.tag AS tag, t.path AS path ' \
                        'FROM case_testobjs AS c INNER JOIN test_objs AS t ' \
                        'ON c.testobj_id = t.id ' \
                        'WHERE c.case_id = %s ' \
                        'ORDER BY c.order'
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(list_test_objs_sql, (case_id,))
        test_objs = cursor.fetchall()

        results = []
        for obj in test_objs:
            temp_obj = {
                'case_id': int(obj[0]),
                'test_obj_id': int(obj[1]),
                'type': str(obj[2]),
                'tag': str(obj[3]),
                'path': str(obj[4])
            }
            results.append(temp_obj)
        return results
    finally:
        cursor.close()


def case_view(request):
    case_id = request.GET.get('case_id', '')
    data={'id': case_id}
    try:
        test_objs = _list_test_objs_by_case_id(case_id)
        print test_objs
    except:
        data = {'is_presentation': True, # hide the nav and footer
            'case_id': case_id,
            'msg': '图片消失在平行的时空',
            'statu': 'None'}
        return render_to_response('management/caseView.html', data)

    assert(0 < len(test_objs) < 3)  # TODO 暂时不支持大于3的情况

    data = {'is_presentation': True, # hide the nav and footer
            'case_id': case_id,
            'test_objs': test_objs}

    return render_to_response('management/caseView.html', data)

@csrf_exempt
def delete_case_testobj_handler(request):
    try:
        case_id = request.POST.get('case_id', '')
        test_obj_id = request.POST.get('testobj_id', '')
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 1, 'msg': 'get request params error'}))

    logger.info('[Request] case_id: %s, testobj_id: %s' % (case_id, test_obj_id))

    if case_id == '':
        logger.warning('case_id is empty')
        return HttpResponse(
            json.dumps({'code': 3, 'msg': 'case_id is empty'}))
    if test_obj_id == '':
        logger.warning('test_obj_id is empty')
        return HttpResponse(
            json.dumps({'code': 3, 'msg': 'test_obj_id is empty'}))

    try:
        case_id = int(case_id)
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 4, 'msg': 'case_id is not  int'}))

    try:
        suite_id = Case.objects.get(pk=case_id).suite_id
        __check_suite_status(suite_id)
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 4, 'msg': 'case does not exist'}))

    try:
        test_obj_id = int(test_obj_id)
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 4, 'msg': 'test_obj_id is not  int'}))

    transaction.set_autocommit(False)
    try:
        case_test_obj = CaseTestObj.objects.get(case_id=case_id,
                                                testobj_id=test_obj_id)
        case_test_obj.delete()
        test_obj_usage_count = CaseTestObj.objects.filter(
            testobj_id=test_obj_id).count()
        if test_obj_usage_count == 0:
            testobj = TestObj.objects.get(pk=test_obj_id, is_locked=1)
            testobj.is_locked = 0
            testobj.save()
        transaction.commit()
    except Exception, e:
        transaction.rollback()
        logger.error(e.message)
        return HttpResponse(
            json.dumps({'code': 6, 'msg': 'delete case_test_obj '
                                          'error'}))

    return HttpResponse(json.dumps({'code': 0, 'msg': 'delete '
                                                      'case_test_obj success'}))


# @csrf_exempt
# def delete_test_obj_handler(request):
#     try:
#         tid = request.POST.get('tid', 0)
#     except Exception, e:
#         logger.exception(e.message)
#         return HttpResponse(json.dumps({'code': 1, 'msg': 'tid is none'}))
#
#     if tid <= 0:
#         return HttpResponse(json.dumps({'code': 2, 'msg': 'tid error'}))
#
#     try:
#         t = TestObj.objects.get(id=tid, is_locked=0)
#         t.delete()
#     except Exception, e:
#         logger.error(e.message)
#         return HttpResponse(json.dumps({'code': 3, 'msg': 'delete exception'}))
#
#     return HttpResponse(json.dumps({'code': 0, 'msg': 'successed'}))


@csrf_exempt
def edit_test_obj_handler(request):
    try:
        tid = request.POST.get('tid', 0)
        app_id = request.POST.get('app_id', 0)
        scene_id = request.POST.get('scene_id', 0)
        tag = request.POST.get('tag', '')
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 1, 'msg': 'get params exception'}))

    if tid <= 0:
        return HttpResponse(json.dumps({'code': 2, 'msg': 'tid is none'}))

    if app_id <= 0:
        return HttpResponse(json.dumps({'code': 3, 'msg': 'app_id is none'}))

    if scene_id <= 0:
        return HttpResponse(json.dumps({'code': 4, 'msg': 'scene_id is none'}))

    to = None
    try:
        to = TestObj.objects.get(id=tid)
    except Exception, e:
        logger.error(e.message)
        return HttpResponse(
            json.dumps({'code': 5, 'msg': 'test_obj not exist'}))

    try:
        app = App.objects.get(id=app_id)
    except Exception, e:
        logger.error(e.message)
        return HttpResponse(json.dumps({'code': 6, 'msg': 'app not exist'}))

    try:
        scene = Scene.objects.get(id=scene_id)
    except Exception, e:
        logger.error(e.message)
        return HttpResponse(json.dumps({'code': 7, 'msg': 'scene not exist'}))

    try:
        to.app_id = app_id
        to.scene_id = scene_id
        to.tag = tag
        to.save()
    except Exception, e:
        logger.error(e.message)
        return HttpResponse(
            json.dumps({'code': 6, 'msg': 'udate testobj error'}))

    return HttpResponse(json.dumps({'code': 0, 'msg': 'success'}))


def test_obj_index(request):
    try:
        tag = request.GET.get('tag', '')
        paginator = {
            'pageNo': int(request.GET.get('page_no', 1)),
            'pageSize': int(request.GET.get('page_size', 20))
        }
    except Exception, e:
        logger.exception(e.message)
        return

    if paginator['pageSize'] < 20:
        paginator['pageSize'] = 20
    if paginator['pageSize'] > 50:
        paginator['pageSize'] = 50

    offset = (paginator['pageNo'] - 1) * paginator['pageSize']
    appMap = {}
    sceneMap = {}
    try:
        test_objs = TestObj.objects.filter(tag__contains=tag).order_by("-id")[
                    offset: offset + paginator['pageSize']]
        paginator['totalCounts'] = TestObj.objects.all().count()
        apps = App.objects.filter().order_by("-id")
        for app in apps:
            appMap[app.id] = app.name

        scenes = Scene.objects.filter().order_by("-id")
        for scene in scenes:
            sceneMap[scene.id] = scene.name
    except Exception, e:
        logging.exception(e.message)
        return

    data = {'test_objs': test_objs,
            'appMap': appMap,
            'sceneMap': sceneMap,
            'tag': tag,
            'paginator': paginator,
            'page_type': 'test_obj_index_page'}
    return render_to_response('management/testObjIndex.html', data)


@csrf_exempt
def disable_test_obj_handler(request):
    try:
        testobj_id = request.POST.get('testobj_id', -1)
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(json.dumps({'code': 1, 'msg': 'get params exception'}))

    try:
        TestObj.objects.filter(pk=testobj_id, is_locked=0).update(is_locked=1)
        # testobj.is_locked = 1
        # testobj.save()
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(
            json.dumps({'code': 2, 'msg': 'diasble test_obj failed, '
                                          'query error'}))

    return HttpResponse(
        json.dumps({'code': 0, 'msg': 'diasble test_obj failed'}))


# chenyixin
def testObj_get_info(request):
    try:
        info = request.GET.get('test_obj_info', '')
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(json.dumps({'code': 1, 'msg': 'get params exception'}))

    appsMap = {}
    scenesMap = {}
    if info == 'info':
        try:
            apps = App.objects.all()
            scenes = Scene.objects.all()
            for app in apps:
                appsMap[app.id] = app.display_name

            for scene in scenes:
                scenesMap[scene.id] = scene.name

        except Exception, e:
            logger.exception(e.message)
            return HttpResponse(json.dumps({'code': 5, 'msg': 'the database error'}))

        data = {'code': 0, 'appsMap': appsMap,
                'scenesMap': scenesMap,
                }

        return HttpResponse(json.dumps(data))
    else:
        return HttpResponse(json.dumps({'code': 6, 'msg': 'the info error'}))


def testObj_get_path(request):
    try:
        obj_id = request.GET.get('obj_id', '')
        path = request.GET.get('test_obj_path', '')
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(json.dumps({'code': 1, 'msg': 'get params exception'}))

    if path == 'path':
        try:
            testObj = TestObj.objects.get(id=obj_id)
            path = testObj.path
            absolute_path = os.path.join(settings.ATTACHMENTS_DIR, path)

        except Exception, e:
            logger.exception(e.message)
            return HttpResponse(json.dumps({'code': 5, 'msg': 'the database error'}))

        print absolute_path
        data = {'code': 0, 'path': absolute_path,
                }

        return HttpResponse(json.dumps(data))
    else:
        return HttpResponse(json.dumps({'code': 6, 'msg': 'the path error'}))


class UploadFileForm(forms.Form):
    app_id = forms.CharField(max_length=255)
    scene_id = forms.CharField(max_length=255)
    tag = forms.CharField(max_length=255, required=False)
    file = forms.FileField()


@csrf_exempt
def handle_uploaded_file(file, file_name, sufix, dict):
    img = ('jpg', 'jpeg', 'png', 'gif', 'bmp')
    vid = ('avi', 'mpg', 'mp4', 'mpeg')
    absolute_path = ''
    relative_path = ''
    type = ''
    sufix = sufix.lower()
    if (sufix in img):
        absolute_path = os.path.join(settings.ATTACHMENTS_DIR, 'test_objects', 'image')
        relative_path = os.path.join('test_objects', 'image')
        type = 'image'
        if not os.path.exists(absolute_path):
            os.makedirs(absolute_path)
    else:
        absolute_path = os.path.join(settings.ATTACHMENTS_DIR, 'test_objects', 'media')
        relative_path = os.path.join('test_objects', 'media')
        type = 'media'
        if not os.path.exists(absolute_path):
            os.makedirs(absolute_path)

    file_name = file_name + "." + sufix
    relative_path = os.path.join(relative_path, file_name)
    absolute_path = os.path.join(absolute_path, file_name)

    with  open(absolute_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
        destination.close()

    # destination = open(absolute_path, 'wb+')
    # for chunk in file.chunks():
    #     destination.write(chunk)
    # destination.close()

    try:
        testObj = TestObj()
        testObj.app_id = dict['app_id']
        testObj.scene_id = dict['scene_id']
        testObj.tag = dict['tag']
        testObj.type = type
        testObj.path = relative_path
        testObj.is_locked = 0
        testObj.save()
    except Exception, e:
        logger.exception(e.message)


@csrf_exempt
def upload_test_obj(request):
    if request.method == 'POST':
        try:
            form = UploadFileForm(request.POST, request.FILES)
            app_id = request.POST.get('app_id', '')
            scene_id = request.POST.get('scene_id', '')
            tag = request.POST.get('tag', '')

            test_obj_info = {'app_id': app_id, 'scene_id': scene_id, 'tag': tag}
        except Exception, e:
            logger.exception(e.message)
            return HttpResponse(json.dumps({'code': 1, 'msg': 'get params exception'}))

        if form.is_valid():
            try:
                for i in request.FILES.keys():
                    f = request.FILES[i]
                    file_name = str(uuid.uuid4())
                    sufix = os.path.splitext(f.name)[1][1:]
                    # file=str(file_name)+"."+sufix
                    handle_uploaded_file(request.FILES[i], file_name, sufix, test_obj_info)
                    print request.FILES[i]
            except Exception, e:
                logger.exception(e.message)
                return HttpResponse(json.dumps({'code': 7, 'msg': 'upload error'}))
            else:
                return HttpResponse(json.dumps({'code': 0, 'msg': 'upload success'}))
        else:
            return HttpResponseBadRequest()
    else:
        return HttpResponse(json.dumps({'code': 7, 'msg': 'method is not post'}))


@csrf_exempt
def test_obj_edit(request):
    id = request.POST.get('id', '')
    app_id = request.POST.get('app_id', '')
    scene_id = request.POST.get('scene_id', '')
    tag = request.POST.get('tag', '')

    try:
        testObj = TestObj.objects.get(id=id)
        testObj.app_id = app_id
        testObj.scene_id = scene_id
        testObj.tag = tag
        testObj.save()
        return HttpResponse(json.dumps({'code': 0, 'msg': 'OK'}))
    except Exception, e:
        logger.exception(e.message)
        return HttpResponse(json.dumps({'code': 4, 'msg': 'edit test_obj error'}))
