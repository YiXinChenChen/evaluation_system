# -*- coding: utf-8 -*-

import json
import logging
import uuid
import urllib

from django.core import urlresolvers
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.shortcuts import render_to_response

from core.models import Case
from core.models import CaseGroup
from core.models import Execution
from core.models import Suite
from core.models import SuiteCurrentGroup
from sqa.forms import UserInfoForm
from sqa.forms import VoteForm

from wechat_open import WeChatOpen


from core.logging import ExecutionLoggerAdapter

# Create your views here.
_logger = logging.getLogger(__name__)


def _get_current_execution(request, suite_uuid):
    '''
    :return:
    '''
    logger = ExecutionLoggerAdapter(_logger, {'request':request, 'execution':None})

    u_id = request.session.get('uid', default=None)
    # 说明没有u_id
    if u_id is None:
        logger.debug('uid is none')
        return None

    logger.debug('get execution by uid %s and suite_uuid %s' % (u_id,suite_uuid))

    execution = None
    try:
        executions = Execution.objects.filter(uid=u_id, suite_uuid=suite_uuid).order_by('-ctime')[:1]
        execution = executions[0] if len(executions) > 0 else None
    except Exception, e:
        logger.exception('error')

    if execution is None:
        logger.debug('execution is none')
    else:
        logger.debug('execution is id=%d' % (execution.id,))
    return execution


def _validate_execution(request, execution, suite_uuid):
    logger = ExecutionLoggerAdapter(_logger, {'request':request, 'execution':execution})

    session_id = request.session.session_key

    logger.debug('execution is None: %s session_id is None: %s' % (execution is None, session_id is None,))
    if execution is None and session_id is None:
        logger.debug('_validate_execution: execution and session_id are None')
        return False

    if execution is not None and session_id is not None:
        logger.debug('execution and session_id are neither None')
        logger.debug('execution.status == "ready": %s execution.session_id == session_id: %s' %
                     (execution.status == 'ready', execution.session_id == session_id,))
        logger.debug('execution uid is %s' % (execution.uid,))
        logger.debug('execution status is %s' % (execution.status,))
        logger.debug('execution session_id is %s' % (execution.session_id,))
        logger.debug('session_id is %s' % (session_id,))

        if not execution.status == 'ready' or not execution.session_id == session_id:
            return False

        logger.debug('execution suite_uuid is %s' % (execution.suite_uuid,))
        logger.debug('suite_uuid is %s' % (suite_uuid,))
        return execution.suite_uuid == suite_uuid

    return False


def _reset_execution(request, execution):
    session_id = request.session.session_key
    token = request.session.get('token', default=None)
    ref = request.session.get('ref', default=None)

    execution.session_id = session_id
    execution.token = token
    execution.refer = ref
    execution.status = 'ready'
    # reset cur_case_index to 0
    context = execution.context
    context_map = json.loads(context)
    context_map["cur_case_index"] = 0
    execution.context = json.dumps(context_map)
    execution.result = json.dumps({})
    execution.version = 0
    execution.save()
    return execution


def _phone_to_hash(ll):
    ll = int(ll)
    set = []
    for i in range(48, 57+1, 1):
        set.append(chr(i))
    for i in range(65, 90+1, 1):
        set.append(chr(i))

    num = ll % 10000000000
    binary = bin(num)
    str_bin = str(binary)[2:]

    if len(str_bin) < 40:
        temp_str = ''

        for i in range(0, 40-len(str_bin), 1):
            temp_str += '0'

        str_bin = temp_str+str_bin

    code = ''
    for i in range(0, 40, 5):
         index = int(str_bin[i:i+5], 2)
         code += set[index]
    return code


def _reverse_welcome_url(request, suite_uuid, inviter_code=None):
    ref = request.session.get('ref', None)

    query_data = {}
    if ref is not None:
        query_data['ref'] = ref
    if inviter_code is not None:
        query_data['inviter_code'] = inviter_code

    redirect_url = urlresolvers.reverse(welcome, kwargs={'suite_uuid': suite_uuid})
    query = urllib.urlencode(query_data)
    return redirect_url if len(query) == 0 else ('?'.join([redirect_url, query]))


def _redirect_to_welcome(request, suite_uuid):
    redirect_url = _reverse_welcome_url(request, suite_uuid)
    return HttpResponseRedirect(redirect_url)


def _reverse_error_url(request, suite_uuid):
    redirect_url = urlresolvers.reverse(error, kwargs={'suite_uuid': suite_uuid})
    return redirect_url


def _redirect_to_error(request, suite_uuid):
    redirect_url = _reverse_error_url(request, suite_uuid)
    return HttpResponseRedirect(redirect_url)


def _submit_execution_result(request, execution, result):
    assert (request is not None and execution is not None)
    logger = ExecutionLoggerAdapter(_logger, {'request':request, 'execution':execution})

    # execution may be out of date
    execution = Execution.objects.get(id=execution.id)

    # get current case index
    context_json = execution.context
    context_map = json.loads(context_json)
    current_case_index = context_map['cur_case_index']
    cases = context_map['cases']
    current_case_id = cases[str(current_case_index)]

    # submit result
    result_json = execution.result
    if result_json is None or len(result_json) == 0:
        result_map = {}
    else:
        result_map = json.loads(result_json)
    key = str(current_case_id)
    if result_map.has_key(key):
        logger.error('ignore result of execution id=%d, case_id=%d, because it has been submitted' % (execution.id, current_case_id,))
        return True
    result_map[key] = result
    result_json = json.dumps(result_map)

    rows = Execution.objects.filter(id=execution.id, version=execution.version).update(result=result_json,
                                                                                       version=execution.version + 1)
    return 1 == rows


def _redirect_next_case(request, suite_uuid, execution, case_id):
    assert (request is not None and suite_uuid is not None and execution is not None)
    logger = ExecutionLoggerAdapter(_logger, {'request':request, 'execution':execution})

    # execution may be out of date
    execution = Execution.objects.get(id=execution.id)

    # update execution context
    context_json = execution.context
    context_map = json.loads(context_json)

    # validate current case id
    cases = context_map['cases']
    current_case_index = context_map['cur_case_index']
    current_case_id = cases[str(current_case_index)]

    case_id = int(case_id)
    if current_case_id == case_id:
        total_case = context_map['total_case']

        if current_case_index + 1 >= total_case:
            # no case any more
            return HttpResponseRedirect(urlresolvers.reverse(submit_user_info, kwargs={'suite_uuid': suite_uuid}))

        # increse cur_case_index
        context_map['cur_case_index'] = current_case_index + 1
        context_json = json.dumps(context_map)

        rows = Execution.objects.filter(id=execution.id, version=execution.version).update(context=context_json,
                                                                                           version=execution.version + 1)
        if 0 == rows:
            logger.error('version may be not fit')
            return HttpResponse(status=500)  # todo ERROR page

    # redirect_url = urlresolvers.reverse(presentation, kwargs={'suite_uuid': suite_uuid}) + '?' + urllib.urlencode(
    #     {'step': 0})
    redirect_url = urlresolvers.reverse(presentation_and_vote, kwargs={'suite_uuid': suite_uuid})
    return HttpResponseRedirect(redirect_url)


def _get_suite_status(suite_uuid):
    try:
        suite = Suite.objects.get(uuid=suite_uuid)
    except Exception, e:
        _logger.exception(e.message)
        raise e
    if suite is not None:
        if suite.status == 'ready' or suite.status == 'testing':
            return True
        elif suite.status == 'finished':
            return False
        else:
            raise Exception('suite status status is :{0}, status value error '.format(suite.status))


def _reverse_suite_end_url(request, suite_uuid):
    return urlresolvers.reverse(suite_end, kwargs={'suite_uuid': suite_uuid})


def _redirect_to_suite_end(request, suite_uuid):
    redirect_url = _reverse_suite_end_url(request, suite_uuid)
    return HttpResponseRedirect(redirect_url)


def index(request):
    # return redirect('welcome')
    return render_to_response('sqa/index.html')


def redirect_to_welcome(request, suite_uuid):
    return _redirect_to_welcome(request, suite_uuid)


def welcome(request, suite_uuid):
    logger = ExecutionLoggerAdapter(_logger, {'request':request, 'execution':None})

    try:
        ref = request.GET.get('ref', None)
        inviter_code = request.GET.get('inviter_code', '')
    except Exception, e:
        logger.exception(e.message)
        return _redirect_to_error(request, suite_uuid)

    if suite_uuid is None:
        logger.error('suite_uuid is None')
        return _redirect_to_error(request, suite_uuid)

    suite = None
    try:
        suite = Suite.objects.get(uuid=suite_uuid)
    except Exception, e:
        logger.exception(e.message)
        return _redirect_to_error(request, suite_uuid)

    if not suite.status == 'testing':
        return _redirect_to_suite_end(request, suite_uuid)

    # create session here
    request.session['ref'] = ref
    request.session['suite_uuid'] = suite_uuid
    # the recommend code
    request.session['inviter_code'] = inviter_code

    # according wechat doc, generate a random string to avoid csrf
    oauth_state = str(uuid.uuid4())
    request.session['oauth_state'] = oauth_state
    request.session.save()

    from django.conf import settings
    wechat_open = WeChatOpen(**(settings.WECHAT_SETTINGS))

    redirect_url = urlresolvers.reverse(wechat_oath_callback, kwargs={'suite_uuid': suite_uuid})
    redirect_url = request.build_absolute_uri(redirect_url)

    qrconnect_url = wechat_open.get_qrconnect_url(redirect_url, state=oauth_state)

    return render_to_response('sqa/welcome.html', {'ref': ref, 'suite': suite, 'qrconnect_url':qrconnect_url})


def wechat_oath_callback(request, suite_uuid):
    logger = ExecutionLoggerAdapter(_logger, {'request':request, 'execution':None})

    code = request.GET.get('code', None)
    state = request.GET.get('state', None)

    if code is None or len(code) == 0:
        # user rejects auth
        logger.info('code is empty, user rejects auth')
        return _redirect_to_welcome(request, suite_uuid)

    if state is None or len(state) == 0:
        logger.error('state is required')
        return _redirect_to_error(request, suite_uuid)

    # check state, as csrf token
    oauth_state = request.session.get('oauth_state', None)
    if oauth_state is None or len(oauth_state) == 0:
        logger.error('session oauth_state is empty')
        return _redirect_to_error(request, suite_uuid)

    if not oauth_state == state:
        logger.error('session oauth_state does not equal to state')
        return _redirect_to_error(request, suite_uuid)

    from django.conf import settings
    wechat_open = WeChatOpen(**(settings.WECHAT_SETTINGS))

    access_token_json = wechat_open.get_access_token(code)
    if access_token_json is None:
        logger.error('sth. wrong with wechat oauth2 api \'access_token\' return empty')
        return _redirect_to_error(request, suite_uuid)

    # token
    access_token = access_token_json.get('access_token', None)
    if access_token is None or len(access_token) == 0:
        logger.error('sth. wrong with wechat oauth2 api \'access_token\', access_token is empty')
        return _redirect_to_error(request, suite_uuid)

    # uid
    uid = access_token_json.get('openid', None)
    if uid is None or len(uid) == 0:
        logger.error('sth. wrong with wechat oauth2 api \'access_token\', openid is empty')
        return _redirect_to_error(request, suite_uuid)

    request.session['token'] = access_token
    request.session['uid'] = uid

    redirect_url = urlresolvers.reverse(intro, kwargs={'suite_uuid': suite_uuid})
    return HttpResponseRedirect(redirect_url)


def intro(request, suite_uuid):
    logger = ExecutionLoggerAdapter(_logger, {'request':request, 'execution':None})

    session_id = request.session.session_key
    uid = request.session.get('uid', default=None)

    if session_id is None or uid is None or suite_uuid is None:
        logger.debug('sth. wrong with session')
        logger.debug('session_id is None=%s, uid is None=%s, suite_uuid is None=%s' % (
            (session_id is None), (uid is None), (suite_uuid is None)))
        return _redirect_to_welcome(request, suite_uuid)

    try:
        suite = Suite.objects.get(uuid=suite_uuid)
        if suite.status == 'ready':
            return _redirect_to_welcome(request, suite_uuid)
        elif suite.status == 'finished':
            return _redirect_to_suite_end(request, suite_uuid)
    except Exception, e:
        logger.exception(e.message)
        return HttpResponseRedirect(urlresolvers.reverse(error, kwargs={'suite_uuid': suite_uuid}))

    return render_to_response('sqa/intro.html', {'suite': suite})


def get_execution(request, suite_uuid):
    logger = ExecutionLoggerAdapter(_logger, {'request':request, 'execution':None})

    try:
        session_id = request.session.session_key
        token = request.session.get('token', default=None)
        u_id = request.session.get('uid', default=None)
        ref = request.session.get('ref', default=None)
        inviter_code = request.session.get('inviter_code', default='')
    except Exception, e:
        logger.exception(e.message)
        redirect_url = _reverse_welcome_url(request, suite_uuid)
        return HttpResponse(json.dumps({'code': 1, 'msg': 'get param error', 'redirect_url': redirect_url}))

    if session_id is None:
        # todo redirect to login
        logger.debug('session_id is None')
        redirect_url = _reverse_welcome_url(request, suite_uuid)
        return HttpResponse(json.dumps({'code': 2, 'msg': 'params error',
                                        'redirect_url': redirect_url}))  # _redirect_to_welcome(request, suite_uuid)
    if token is None:
        # todo redirect to login
        logger.debug('token is None')
        redirect_url = _reverse_welcome_url(request, suite_uuid)
        return HttpResponse(json.dumps({'code': 3, 'msg': 'params error',
                                        'redirect_url': redirect_url}))  # _redirect_to_welcome(request, suite_uuid)
    if u_id is None:
        # todo redirect to login
        logger.debug('u_id is None')
        redirect_url = _reverse_welcome_url(request, suite_uuid)
        return HttpResponse(json.dumps({'code': 4, 'msg': 'params error',
                                        'redirect_url': redirect_url}))  # _redirect_to_welcome(request, suite_uuid)
    if suite_uuid is None:
        # todo redirect to login
        logger.debug('suite_uuid is None')
        redirect_url = _reverse_welcome_url(request, suite_uuid)
        return HttpResponse(json.dumps({'code': 5, 'msg': 'params error',
                                        'redirect_url': redirect_url}))  # _redirect_to_welcome(request, suite_uuid)

    try:
        suite_usable = _get_suite_status(suite_uuid)

        if suite_usable is False:
            # suite is finished redirect to activity end page
            redirect_url = _reverse_suite_end_url(request, suite_uuid)
            return HttpResponse(json.dumps({'code': 7, 'msg': 'params error', 'redirect_url': redirect_url}))

        execution = _get_current_execution(request, suite_uuid)
        if execution is not None:
            # has execution, validate it

            if execution.status == 'finished':
                # 1. finished execution, jump to has_been_finished
                redirect_url = urlresolvers.reverse(has_been_finished, kwargs={'suite_uuid': suite_uuid})
                return HttpResponse(json.dumps({'code': 8, 'msg': 'params error', 'redirect_url': redirect_url}))

            if execution.session_id != session_id:
                # 2. session id is not the same
                # may be the situation as follow:
                # a) session expired, a new session is created
                # b) two browser
                # simply, we just set execution.session_id = session_id
                # so:
                # a) continue the progress
                # b) old browser has to re-login, new browser continue the progress
                Execution.objects.filter(id=execution.id, session_id=execution.session_id).update(session_id=session_id)

            return HttpResponse(json.dumps({'code': 0, 'msg': 'execution exist and legal'}))
        else:
            # no execution, need create

            # get user info from we chat
            from django.conf import settings
            wechat_open = WeChatOpen(**(settings.WECHAT_SETTINGS))
            userinfo_json = wechat_open.get_userinfo(token, u_id)

            # 1. get suite by suite_uuid
            suite = Suite.objects.get(uuid=suite_uuid)
            suite_id = suite.id

            # 2. get group get bucket according suite.cur_group_index%len(groups)
            case_groups = CaseGroup.objects.filter(suite_id=suite_id).order_by('id')

            if case_groups is None or len(case_groups) == 0:
                raise RuntimeError('get suite group error')

            # 3. increase suite.cur_group_index
            # why not in transaction? because that will too complicated
            cur_group_index = SuiteCurrentGroup(suite_id).get_and_increase()

            # 4. start transaction
            # use transaction.atomic rather than transaction.set_autocommit
            # any exception raised in the transaction.atomic will cause rollback
            # if use transaction.set_autocommit, we have to restore it
            # according to: https://docs.djangoproject.com/en/1.9/topics/db/transactions/
            with transaction.atomic():
                cur_bucket = cur_group_index % (len(case_groups))
                target_group_id = case_groups[cur_bucket].id

                # 5. get case.id in random
                cases = Case.objects.filter(suite_id=suite_id).filter(group_id=target_group_id).order_by('?')
                if cases is None or len(cases) == 0:
                    raise RuntimeError('get suite case error')

                case_ids = [case.id for case in cases]

                case_id_map = {}
                for i in range(0, len(case_ids)):
                    case_id_map[i] = case_ids[i]

                # 6. create execution
                context_map = {}
                context_map['cases'] = case_id_map
                context_map['cur_case_index'] = 0
                context_map['total_case'] = len(cases)

                execution = Execution()
                execution.uid = u_id
                execution.token = token
                execution.username = userinfo_json['nickname'] if 'nickname' in userinfo_json else ''
                execution.refer = ref
                execution.session_id = session_id
                execution.status = 'ready'
                execution.suite_id = suite_id
                execution.suite_uuid = suite_uuid
                execution.inviter_code = inviter_code
                execution.context = json.dumps(context_map)
                execution.version = 0
                execution.save()

                return HttpResponse(json.dumps({'code': 0, 'msg': 'create execution success'}))
    except Exception, e:
        logger.exception("")
        redirect_url = _redirect_to_error(request, suite_uuid)
        return HttpResponse(json.dumps({'code': 11, 'msg': 'get execution error', 'redirect_url': redirect_url}))


def presentation(request, suite_uuid):
    logger = ExecutionLoggerAdapter(_logger, {'request':request, 'execution':None})

    try:
        suite_usable = _get_suite_status(suite_uuid)
    except Exception, e:
        logger.exception(e.message)
        # get suite suite status error redirect to welcome page
        return redirect_to_welcome(request, suite_uuid)
    if suite_usable is False:
        # suite is finished redirect to activity end page
        return _redirect_to_suite_end(request, suite_uuid)

    execution = _get_current_execution(request, suite_uuid)
    if _validate_execution(request, execution, suite_uuid) is False:
        logger.error('execution invalid')
        return _redirect_to_welcome(request, suite_uuid)

    logger = ExecutionLoggerAdapter(_logger, {'request':request, 'execution':execution})
    # exec有效，开始测试
    try:
        step = int(request.GET.get('step', 0))
    except Exception, e:
        logger.exception(e.message)
        return _redirect_to_welcome(request, suite_uuid)

    logger.debug('Request execution: %s step: %s' % (execution, step,))

    try:
        context = json.loads(execution.context)
        logger.debug(context)
    except Exception, e:
        logger.error(e.message)
        # todo 改为重定向到错误页面
        return _redirect_to_error(request, suite_uuid)

    try:
        case_id = context['cases'][str(context['cur_case_index'])]

        from django.db import connection
        search_sql_str = 'select ' \
                         'c.case_id as case_id, t.id as test_obj_id, t.type as type, t.tag as tag, t.path as path ' \
                         'from case_testobjs as c inner join test_objs as t ' \
                         'on c.testobj_id = t.id ' \
                         'where c.case_id = %s ' \
                         % case_id
        cursor = connection.cursor()
        cursor.execute(search_sql_str)
        test_objs = cursor.fetchall()
        cursor.close()

        objects = []
        try:
            for obj in test_objs:
                temp_obj = {
                    'case_id': int(obj[0]),
                    'test_obj_id': int(obj[1]),
                    'type': str(obj[2]),
                    'tag': str(obj[3]),
                    'path': str(obj[4])
                }
                objects.append(temp_obj)
        except Exception, e:
            logger.exception(e.message)
            return _redirect_to_error(request, suite_uuid)

    except Exception, e:
        logger.exception(e.message)
        return _redirect_to_error(request, suite_uuid)

    if step >= len(test_objs):
        logger.error('step more than test_objs length')
        # todo 改为重定向到错误页面
        return _redirect_to_error(request, suite_uuid)

    data = {'is_presentation': False, 'suite_uuid': suite_uuid,
            'test_obj': objects[step], 'step': step, 'total': len(objects) - 1, 'case_id': case_id, 'last': step - 1,
            'next': step + 1}
    logger.info('Response data: %s' % (data,))

    # return render_to_response('sqa/presentation.html', data)
    return render(request, 'sqa/presentation.html', data)


def _get_current_cases(execution):
    context = json.loads(execution.context)
    return context['cases']


def _get_current_case_index(execution):
    context = json.loads(execution.context)
    return context['cur_case_index']


def _get_current_case_id(execution):
    context = json.loads(execution.context)
    current_case_index = str(context['cur_case_index'])
    cases = context['cases']
    return cases[current_case_index]


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


def _get_execution_result(execution):
    return json.loads(execution.result)


def presentation_and_vote(request, suite_uuid):
    logger = ExecutionLoggerAdapter(_logger, {'request':request, 'execution':None})
    try:
        suite_usable = _get_suite_status(suite_uuid)
    except Exception, e:
        logger.exception(e.message)
        # get suite suite status error redirect to welcome page
        return _redirect_to_error(request, suite_uuid)
    if suite_usable is False:
        # suite is finished redirect to activity end page
        return _redirect_to_suite_end(request, suite_uuid)

    execution = _get_current_execution(request, suite_uuid)
    if _validate_execution(request, execution, suite_uuid) is False:
        logger.error('execution invalid')
        return _redirect_to_welcome(request, suite_uuid)

    logger = ExecutionLoggerAdapter(_logger, {'request':request, 'execution':execution})
    try:
        cases = _get_current_cases(execution)
        current_case_index = _get_current_case_index(execution)
        case_id = _get_current_case_id(execution)
        test_objs = _list_test_objs_by_case_id(case_id)
    except Exception, e:
        logger.exception(e.message)
        return _redirect_to_error(request, suite_uuid)

    assert(0 < len(test_objs) < 3)  # TODO 暂时不支持大于3的情况

    data = {'is_presentation': True, # hide the nav and footer
            'suite_uuid': suite_uuid,
            'case_id': case_id, 'case_index': current_case_index + 1, 'case_count': len(cases),
            'test_objs': test_objs}
    response = render(request, 'sqa/presentation_and_vote.html', data)
    response.cookies['case_id'] = case_id # TODO 好像没啥用
    return response


def vote(request, suite_uuid):
    if not request.method == 'POST':
        return HttpResponse(status=405)

    logger = ExecutionLoggerAdapter(_logger, {'request':request, 'execution':None})
    try:
        suite_usable = _get_suite_status(suite_uuid)
    except Exception, e:
        logger.exception(e.message)
        # get suite suite status error redirect to welcome page
        return _redirect_to_error(request, suite_uuid)
    if suite_usable is False:
        # suite is finished redirect to activity end page
        return _redirect_to_suite_end(request, suite_uuid)

    execution = _get_current_execution(request, suite_uuid)
    if not _validate_execution(request, execution, suite_uuid):
        return _redirect_to_welcome(request, suite_uuid)

    logger = ExecutionLoggerAdapter(_logger, {'request':request, 'execution':execution})
    form = VoteForm(request.POST)
    if form.is_valid():
        logger.debug('vote form is valid')
        if not _submit_execution_result(request, execution, form.cleaned_data['vote']):
            logger.debug('submit execution result failed')
            return _redirect_to_error(request, suite_uuid)
        logger.debug('submit execution result ok, redirect to next case')
        return _redirect_next_case(request, suite_uuid, execution, form.cleaned_data['case_id'])
    else:
        logger.debug('vote form is not valid')
        return _redirect_to_error(request, suite_uuid)


def submit_user_info(request, suite_uuid):
    logger = ExecutionLoggerAdapter(_logger, {'request':request, 'execution':None})
    try:
        suite_usable = _get_suite_status(suite_uuid)
    except Exception, e:
        logger.exception(e.message)
        # get suite suite status error redirect to welcome page
        return _redirect_to_error(request, suite_uuid)
    if suite_usable is False:
        # suite is finished redirect to activity end page
        return _redirect_to_suite_end(request, suite_uuid)

    execution = _get_current_execution(request, suite_uuid)
    if not _validate_execution(request, execution, suite_uuid):
        return _redirect_to_welcome(request, suite_uuid)

    logger = ExecutionLoggerAdapter(_logger, {'request':request, 'execution':execution})
    # must validate that all case has result
    cases = _get_current_cases(execution)
    result = _get_execution_result(execution)
    if len(cases) != len(result):
        return HttpResponseRedirect(urlresolvers.reverse(presentation_and_vote, kwargs={'suite_uuid': suite_uuid}))

    if not request.method == 'POST':
        form = UserInfoForm()
        return render(request, 'sqa/user_info.html', {'form': form})

    form = UserInfoForm(request.POST)
    if not form.is_valid():
        logger.debug('form is not valid')
        return render(request, 'sqa/user_info.html', {'form': form})

    logger.debug('update execution')
    data = form.cleaned_data
    invite_code = _phone_to_hash(data['phone'])
    # print invite_code
    logger.debug('update execution invitation code %s', invite_code)
    rows = Execution.objects.filter(id=execution.id, version=execution.version).update(phone=data['phone'],
                                                                                       yy=data['yy'],
                                                                                       status='finished',
                                                                                       invite_code=invite_code,
                                                                                       version=execution.version + 1)
    if 0 == rows:
        logger.error('submit_user_info: version may be not fit')
        return _redirect_to_error(request, suite_uuid)

    return HttpResponseRedirect(urlresolvers.reverse(thx, kwargs={'suite_uuid': suite_uuid}))


def _clear_session(request):
    for key in request.session.keys():
        if key not in ['token', 'uid']:  # do not clear token and uid
            del request.session[key]
    request.session.clear()
    request.session.flush()


def _get_invitation_url(request, execution):
    invitation_url = _reverse_welcome_url(request, execution.suite_uuid, inviter_code=execution.invite_code)
    invitation_url = request.build_absolute_uri(invitation_url)
    return invitation_url


def thx(request, suite_uuid):
    logger = ExecutionLoggerAdapter(_logger, {'request':request, 'execution':None})

    execution = _get_current_execution(request, suite_uuid)

    if execution is None:
        return _redirect_to_welcome(request, suite_uuid)

    invitation_url = _get_invitation_url(request, execution)

    _clear_session(request)
    return render_to_response('sqa/thx.html', {'invitation_url': invitation_url})


def suite_end(request, suite_uuid):
    _clear_session(request)
    return render_to_response('sqa/suite_end.html', {})


def error(request, suite_uuid):
    _clear_session(request)
    return render_to_response('sqa/error.html')


def has_been_finished(request, suite_uuid):
    logger = ExecutionLoggerAdapter(_logger, {'request':request, 'execution':None})

    msg = 1
    # msg = '您目前成功推荐参与本次测评活动的人数为'

    execution = _get_current_execution(request, suite_uuid)
    if execution is None:
        return _redirect_to_welcome(request, suite_uuid)

    try:
        invite_code = execution.invite_code
        invitation_url = _get_invitation_url(request, execution)
        count = Execution.objects.filter(inviter_code=invite_code).filter(status='finished').count()
    except Exception, e:
        logger.exception(e.message)
        msg = 0
        # msg = '系统错误原因查不到您成功推荐的人数'

    _clear_session(request)
    return render_to_response('sqa/has_been_finished.html', {'msg': msg, 'count': count, 'invitation_url': invitation_url})


def debug(request, suite_uuid):
    '''
    调试页面, 输出调试信息
    :param request:
    :return:
    '''
    suite = Suite.objects.get(uuid=suite_uuid)
    execution = _get_current_execution(request, suite_uuid)

    from django.conf import settings
    wechat_open = WeChatOpen(**(settings.WECHAT_SETTINGS))
    userinfo_json = wechat_open.get_userinfo(execution.token, execution.uid)

    context = {'suite_uuid':suite_uuid, 'execution': execution, 'userinfo': userinfo_json}
    return render_to_response('sqa/debug.html', context)
