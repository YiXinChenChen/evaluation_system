from __future__ import unicode_literals

from django.db import models
import uuid
import threading


# Create your models here.


class CaseGroup(models.Model):
    id = models.AutoField(primary_key=True)
    suite_id = models.IntegerField()
    name = models.CharField(max_length=128)
    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)

    def to_dict(self):
        data = {
            'id': self.id,
            'suite_id': self.suite_id,
            'name': self.name,
            'ctime': self.ctime,
            'mtime': self.mtime,
        }
        return data

    class Meta:
        db_table = 'case_groups'


class CaseTestObj(models.Model):
    id = models.AutoField(primary_key=True)
    case_id = models.IntegerField()
    testobj_id = models.IntegerField()
    order = models.IntegerField()

    def to_dict(self):
        data = {
            'id': self.id,
            'case_id': self.case_id,
            'testobj_id': self.testobj_id,
            'order': self.order,
        }
        return data

    class Meta:
        db_table = 'case_testobjs'


class Case(models.Model):
    id = models.AutoField(primary_key=True)
    suite_id = models.IntegerField()
    group_id = models.IntegerField()
    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)
    remark = models.TextField()

    def to_dict(self):
        data = {
            'id': self.id,
            'suite_id': self.suite_id,
            'group_id': self.group_id,
            'ctime': self.ctime,
            'mtime': self.mtime,
            'remark': self.remark
        }
        return data

    class Meta:
        db_table = 'cases'


class Execution(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.CharField(max_length=64)
    token = models.CharField(max_length=256)  # the length of wechat access_token is 107
    session_id = models.CharField(max_length=64)
    username = models.CharField(max_length=64)
    context = models.TextField()
    result = models.TextField()
    phone = models.CharField(max_length=16)
    yy = models.CharField(max_length=32)
    email = models.CharField(max_length=32)
    inviter_code = models.CharField(max_length=16)
    invite_code = models.CharField(max_length=16)
    refer = models.CharField(max_length=64)
    suite_id = models.IntegerField()
    suite_uuid = models.CharField(max_length=64)
    status = models.CharField(max_length=16)
    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)
    version = models.IntegerField()
    remark = models.TextField()

    def to_dict(self):
        data = {
            'id': self.id,
            'uid': self.info,
            'token': self.token,
            'session_id': self.session_id,
            'username': self.username,
            'context': self.context,
            'result': self.result,
            'phone': self.phone,
            'email': self.email,
            'inviter_code': self.inviter_code,
            'invite_code': self.invite_code,
            'refer': self.refer,
            'suite_id': self.suite_id,
            'ctime': self.ctime,
            'mtime': self.mtime,
            'remark': self.remark
        }
        return data

    class Meta:
        db_table = 'executions'


class Suite(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    split_type = models.CharField(max_length=16)
    case_obj_count = models.IntegerField()
    status = models.CharField(max_length=64)
    cur_group_index = models.IntegerField(default=1)
    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)
    start_date = models.DateField()
    end_date = models.DateField()
    case_count = models.IntegerField()
    remark = models.TextField()

    def to_dict(self):
        data = {
            'id': self.id,
            'uuid': self.info,
            'name': self.name,
            'split_type': self.split_type,
            'case_obj_count': self.case_obj_count,
            'status': self.status,
            'cur_group_index': self.cur_group_index,
            'ctime': self.ctime,
            'mtime': self.mtime,
            'remark': self.remark
        }
        return data

    class Meta:
        db_table = 'suites'


def SuiteCurrentGroup(id):
    return _SuiteCurrentGroup.get_instance(id)


class _SuiteCurrentGroup:
    _class_lock = threading.Lock()
    _instances = {}

    def __init__(self, id):
        self.id = id
        self._lock = threading.Lock()
        self._inited = False
        self._index = None

    @classmethod
    def get_instance(cls, id):
        if id not in cls._instances:
            with cls._class_lock:
                if id not in cls._instances:
                    cls._instances[id] = _SuiteCurrentGroup(id)

        return cls._instances[id]

    def _do_init(self):
        if self._inited:
            return

        with self._lock:
            if not self._inited:
                # todo use other way, do not put this inside the lock
                cur_group_index_list = Suite.objects.filter(id=self.id).values_list('cur_group_index', flat=True)
                self._index = cur_group_index_list[0]
                self._inited = True

    def get_and_increase(self):
        self._do_init()

        with self._lock:
            old_value = self._index
            self._index += 1
            # todo use other way, do not put this inside the lock
            Suite.objects.filter(id=self.id).update(cur_group_index=self._index)

        return old_value



class App(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)
    remark = models.TextField()

    def to_dict(self):
        data = {
            'id': self.id,
            'display_name': self.display_name,
            'ctime': self.ctime,
            'mtime': self.mtime,
            'remark': self.remark
        }
        return data

    class Meta:
        db_table = 'apps'


class Scene(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)
    remark = models.TextField()

    def to_dict(self):
        data = {
            'id': self.id,
            'ctime': self.ctime,
            'mtime': self.mtime,
            'remark': self.remark
        }
        return data

    class Meta:
        db_table = 'scenes'


class TestObj(models.Model):
    id = models.AutoField(primary_key=True)
    app_id = models.IntegerField()
    scene_id = models.IntegerField()
    type = models.CharField(max_length=16)
    is_locked = models.IntegerField()
    tag = models.CharField(max_length=255)
    path = models.CharField(max_length=255)
    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)
    remark = models.TextField()

    def to_dict(self):
        data = {
            'id': self.id,
            'app_id': self.app_id,
            'scene_id': self.scene_id,
            'type': self.type,
            'is_locked': self.is_locked,
            'tag': self.tag,
            'path': self.path,
            'ctime': self.ctime,
            'mtime': self.mtime,
            'remark': self.remark
        }
        return data

    class Meta:
        db_table = 'test_objs'
