# -*- coding:utf-8 -*-
import os
import logging
import uuid
import sys
import cv2
import numpy

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from core.models import TestObj, App, Scene, Suite, CaseGroup, Case, CaseTestObj
from datetime import datetime

# TODO 确认服务器系统
# from cut import removeMargin

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    can_import_settings = True

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.suite_name = None
        self.test_obj_path = None
        self.test_obj_basedir = None
        self.remark_suffix = None
        self.remark_split = None

        self.case_grouping = None
        self.case_obj_count = 0

        self.test_obj_cutting = None

        self.apps = []
        self.scenes = []
        self.suite = None
        self.groups = []
        self.cases = []
        self.caset_testobjs = []

    def add_arguments(self, parser):
        parser.add_argument('--remark-suffix', default='AUTO_CREATE')
        parser.add_argument('--remark-split', default='#*')
        parser.add_argument('--case-grouping', default='MOBILE_LIVE_APP5_COMP2')
        parser.add_argument('--test-obj-cutting', default=None, type=str)
        parser.add_argument('suite_name')
        parser.add_argument('test_obj_path')

    def handle(self, *args, **options):
        self.suite_name = options['suite_name']
        self.test_obj_path = options['test_obj_path']
        self.remark_suffix = options['remark_suffix'] + str(datetime.now())
        self.remark_split = options['remark_split']

        from django.conf import settings
        self.test_obj_basedir = settings.ATTACHMENTS_DIR

        case_grouping = options['case_grouping']
        self.case_grouping = settings.CASE_GROUPING[case_grouping]
        self.case_obj_count = len(self.case_grouping[0][0])

        test_obj_cutting = options['test_obj_cutting']
        if test_obj_cutting is not None:
            self.test_obj_cutting = settings.TEST_OBJ_CUTTING[test_obj_cutting]

        test_obj_relpath = os.path.relpath(self.test_obj_path, self.test_obj_basedir)
        if test_obj_relpath.startswith('..'):
            raise CommandError('test_obj_path must be relative with ATTACHMENTS_DIR = %s' % self.test_obj_basedir)

        with transaction.atomic():
            self.apps = App.objects.all()
            self.scenes = Scene.objects.all()

            self.create_testobj()
            self.create_suite()
            self.create_case_group()
            self.create_case()
            self.add_testobj_to_case()

    def _cut_testobj(self, testobj_path):
        if self.test_obj_cutting is None:
            return
        platform = os.path.basename(os.path.dirname(testobj_path))
        if platform not in self.test_obj_cutting:
            return
        cutting = self.test_obj_cutting[platform]

        x = cutting['x'] if 'x' in cutting else 0
        y = cutting['y'] if 'y' in cutting else 0

        testobj_image = cv2.imread(testobj_path)
        width = cutting['width'] if 'width' in cutting else testobj_image.size[1] - x
        height = cutting['height'] if 'height' in cutting else testobj_image.size[0] - y

        cut_image = testobj_image[y:y+height, x:x+width]
        cv2.imwrite(testobj_path, cut_image)

    def create_testobj(self):
        # example pic name: me-nl-ios-ip5s-1.png
        for folder in os.listdir(self.test_obj_path):
            for pic in os.listdir(os.path.join(self.test_obj_path, folder)):
                self._cut_testobj(os.path.join(self.test_obj_path, folder, pic))

                try:
                    pic_info = pic.split('.')[0].split('-')
                    app_id = self._find_app(pic_info[0])
                    scene_id = self._find_scene('-'.join(pic_info[1:3]))

                    testobj = TestObj()
                    testobj.app_id = app_id
                    testobj.scene_id = scene_id
                    testobj.type = 'image'
                    testobj.is_locked = 0
                    testobj.path = os.path.relpath(os.path.join(self.test_obj_path, folder, pic), self.test_obj_basedir)

                    testobj.tag = '-'.join(pic_info[0: 3]) # me-nl-ios
                    # 通过remark可以查找到一个唯一的testobj
                    # example: me-nl-android#*...
                    testobj.remark = testobj.tag + self.remark_split + self.remark_suffix
                    testobj.save()
                except Exception, e:
                    logger.exception('create testobj failed')
                    logger.exception(e)
                    trace = sys.exc_info()[2]
                    raise CommandError('create testobj failed'), None, trace

    def create_suite(self):
        try:
            suite = Suite()
            suite.uuid = str(uuid.uuid4())
            suite.name = self.suite_name
            suite.split_type = 'manually'
            suite.case_obj_count = self.case_obj_count
            suite.status = 'ready'
            suite.cur_group_index = 0
            suite.save()

            self.suite = suite
        except Exception, e:
            logger.exception('create suit failed')
            logger.exception(e)
            trace = sys.exc_info()[2]
            raise CommandError('create suit failed'), None, trace

    def create_case_group(self):
        for index in range(len(self.case_grouping)):
            try:
                case_group = CaseGroup()
                case_group.suite_id = self.suite.id
                case_group.name = 'Group ' + str(index + 1)
                case_group.save()
                self.groups.append(case_group)
            except Exception, e:
                logger.exception('create case_group failed')
                logger.exception(e)
                trace = sys.exc_info()[2]
                raise CommandError('create case_group failed'), None, trace

    def create_case(self):
        for group_index in range(len(self.case_grouping)):
            group = self.case_grouping[group_index]
            for case_index in range(len(group)):
                try:
                    case = Case()
                    case.suite_id = self.suite.id
                    case.group_id = self.groups[group_index].id
                    # 根据case的remark可以查找到需要的testonj
                    # example： me-nl-android-mi4#*yy-nl-android-mi4#*...
                    remark_str = ''
                    for pic_index in range(self.case_obj_count):
                        remark_str += group[case_index][pic_index] + self.remark_split

                    case.remark = remark_str + self.remark_suffix
                    case.save()
                    self.cases.append(case)
                except Exception, e:
                    logger.exception('create case failed')
                    logger.exception(e)
                    trace = sys.exc_info()[2]
                    raise CommandError('create case failed'), None, trace

    def add_testobj_to_case(self):
        for case in self.cases:
            try:
                pics = case.remark.split(self.remark_split)
                for index in range(self.case_obj_count):
                    case_testobj = CaseTestObj()
                    # 当且仅当存在这样一条记录时可以正常执行，否则抛出异常
                    testobj = TestObj.objects.get(remark=('-'.join(pics[index].split('-')[0: 3]) + self.remark_split + self.remark_suffix))
                    case_testobj.case_id = case.id
                    case_testobj.testobj_id = testobj.id
                    case_testobj.order = index
                    case_testobj.save()
                    self.caset_testobjs.append(case_testobj)
            except Exception, e:
                logger.exception('add testobj to case failed')
                logger.exception(e)
                trace = sys.exc_info()[2]
                raise CommandError('add testobj to case failed'), None, trace

    def _find_app(self, app_name):
        for app in self.apps:
            if app.name == app_name:
                return app.id
        return None

    def _find_scene(self, scene_name):
        for scene in self.scenes:
            if scene.name == scene_name:
                return scene.id
        return None
