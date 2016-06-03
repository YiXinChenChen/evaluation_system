from django.conf.urls import patterns, include, url
import views

urlpatterns = [
    url(r'^$', views.suite_index),
    url(r'^index$', views.suite_index),
    url(r'^suite_index$', views.suite_index),

    url(r'^add_suite$', views.add_suite_handler),
    url(r'^edit_suite$', views.edit_suite_handler),
    url(r'^start_suite$', views.start_suite_handler),
    url(r'^finish_suite$', views.finish_suite_handler),

    url(r'^suite_group_index$', views.suite_group_index),
    url(r'^add_suite_group$', views.add_suite_group),
    url(r'^edit_group$', views.edit_group),
    url(r'^delete_group$', views.delete_group),

    url(r'^add_case_index$', views.add_case_index),
    url(r'^add_case_testobj$', views.add_case_testobj_handler),
    url(r'^case_testObj_get_order$', views.case_testObj_get_order),
    url(r'^case_testObj_sub_order$', views.case_testObj_sub_order),
    url(r'^case_view$', views.case_view),
    url(r'^add_case$', views.add_case_handler),
    url(r'^delete_case$', views.delete_case_handler),
    url(r'edit_cases$', views.add_case_index),
    url(r'^delete_case_testobj$', views.delete_case_testobj_handler),

    url(r'^scene_index$', views.scene_index),
    url(r'^scene_edit_add$', views.scene_edit_add),

    url(r'^test_obj_index$', views.test_obj_index),
    url(r'^edit_test_obj_handler$', views.edit_test_obj_handler),
    # url(r'^delete_test_obj_handler$', views.delete_test_obj_handler),
    url(r'^disable_test_obj$', views.disable_test_obj_handler),

    # chenyixin
    url(r'^test_obj_add$', views.upload_test_obj),
    url(r'^test_obj_edit$', views.test_obj_edit),
    url(r'^testObj_get_info$', views.testObj_get_info),
    url(r'^testObj_get_path$', views.testObj_get_path),


    url(r'^app_index$', views.app_index),
    url(r'^add_app$', views.add_app_handler),
    url(r'^edit_app$', views.edit_app_handler),
    url(r'^delete_app$', views.delete_app_handler),


]
