# -*- coding: utf-8 -*-
"""User views."""
from flask import Blueprint, render_template, url_for, current_app, redirect,\
	request,flash, session, jsonify, abort
from flask_login import login_required,login_user,current_user
import time,random,json
from sqlalchemy import desc
from flask_wechatpy import oauth

import datetime as dt

from .models import User,Role,Permission,Roles
from ..public.models import *
from ..decorators import permission_required
from log import logger
from ..extensions import wechat,csrf_protect
from .forms import SendLeaveForm
from .create_menu_info import *
from school.utils import templated,flash_errors

blueprint = Blueprint('user', __name__, url_prefix='/users')


@blueprint.route('/')
@templated()
@login_required
def members():
	"""List members."""
	
	return dict()

@blueprint.route('/set_roles')
@login_required
@templated()
def set_roles():
	if current_user.role:
		return ''
	school = School.query.filter_by(active=True).order_by(desc('id')).all()
	return dict(school=school)


@blueprint.route('/set_roles_post',methods=["POST"])
@login_required
def set_roles_post():

	school_id = request.form.get('school_id','0')
	role_id = request.form.get('role_id','0')
	number = request.form.get('number','0')
	verify = request.form.get('verify','0')
	phone = request.form.get('phone','0')
	name = request.form.get('name','')

	school = School.query.get_or_404(school_id)
	#教师
	if int(role_id) ==1:
		if verify != current_app.config['REGISTERVERIFY']:
			flash(u'校验码错误','danger')
			return redirect(url_for('public.home'))
		role = Role.query.filter_by(name='Teacher').first()
		current_user.update(phone=phone,roles=role,schools=school,first_name=name)
		ChargeTeacher.create(number=number,users=current_user)
		flash(u'您已设置角色为“教师”。','success')
		create_teacher_menu()
	#学生
	if int(role_id)==0:
		role = Role.query.filter_by(name='Students').first()
		student = Student.query.filter_by(number=number).filter_by(name=name).first()
		if not student:
			flash(u'姓名与学号不符合，请重新输入','danger')
			return redirect(url_for('public.home'))
		student.update(users=current_user)
		current_user.update(phone=phone,roles=role,schools=school,first_name=name)
		flash(u'您已设置角色为“学生”。','success')
		create_student_menu()
	#家长
	if int(role_id)==2:
		role = Role.query.filter_by(name='Patriarch').first()
		student = Student.query.filter_by(number=number).filter_by(name=name).first()
		if not student:
			flash(u'姓名与学号不符合，请重新输入','danger')
			return redirect(url_for('public.home'))
		sp = StudentParent.create(users=current_user)
		student.update(parents=sp)
		current_user.update(phone=phone,roles=role,schools=school,first_name=name+'的家长')
		flash(u'您已设置角色为“%s”的家长。'%name,'success')
		create_patriarch_doorkeeper__menu()
	#门卫
	if int(role_id)==3:
		if verify != current_app.config['REGISTERVERIFY']:
			flash(u'校验码错误','danger')
			return redirect(url_for('public.home'))
		role = Role.query.filter_by(name='Doorkeeper').first()
		current_user.update(phone=phone,roles=role,schools=school,first_name=name)
		Doorkeeper.create(number=number,users=current_user)
		flash(u'您已设置角色为“校警”。','success')
		create_patriarch_doorkeeper__menu()
	
	return redirect(url_for('public.home'))


#发起请假
@blueprint.route('/send_leave',methods=['GET'])
@templated()
@login_required
@permission_required(Permission.LEAVE)
def send_leave():
	form = SendLeaveForm()
	return dict(form=form)


@blueprint.route('/send_leave_post',methods=['POST'])
@login_required
@permission_required(Permission.LEAVE)
def send_leave_post():

	form = SendLeaveForm()

	if not form.validate_on_submit():
		flash_errors(form)
		return redirect(url_for('.members'))

	number = form.number.data
	ask_start_time = form.start_time.data
	ask_end_time = form.end_time.data
	why = form.why.data

	if not number:
		try:
			number = current_user.student.number
		except Exception as e:
			flash(u'请输入学号')
			return redirect(url_for('.members'))
		
	student = Student.query\
		.join(Classes,Classes.id==Student.classesd) \
		.join(Grade,Grade.id==Classes.grades) \
		.join(School,School.id==Grade.school) \
		.filter(School.id==current_user.school)\
		.filter(Student.number==number)\
		.first()
	if not student:
		flash(u'没有该学生,请重新输入正确的学号。','danger')
		return redirect(url_for('.members'))

	
	if AskLeave.query.filter_by(ask_student=student).filter(AskLeave.charge_state.in_([0,1])).first():
		flash(u'该请假人已经存在请假申请，不能再次发起申请。','danger')
		return redirect(url_for('.members'))

	roles = Role.query.all()
	ask_state = 0

	for i in roles:
		if i == current_user.roles and i.name == 'Students':
			if current_user !=student.users:
				flash(u'你也是学生不能帮其他同学请假的哟。','danger')
				return redirect(url_for('.members'))

		if i == current_user.roles and i.name == 'Patriarch':
			if student.parents.users != current_user:
				flash(u'您是家长只能给自己家的小孩请假哟。','danger')
				return redirect(url_for('.members'))

		#如果为教师 默认同意 请假
		if i == current_user.roles and i.name == 'Teacher':
			ask_state = 1
	
	
	try:
		banzhuren = student.classes.teacher.users
	except Exception as e:
		flash(u'该班级未设置班主任。不能请假','danger')
		return redirect(url_for('.members'))
	
	ask = AskLeave.create(
		send_ask_user=current_user,
		ask_student = student,
		charge_ask_user = banzhuren,
		ask_start_time = ask_start_time,
		ask_end_time = ask_end_time,
		why = why,
		charge_state = ask_state
	)
	
	#此处增加微信通知班主任和家长
	#如果等于1 就是教师发起默认不 微信通知了
	if ask_state !=1:
		try:
			teacher_wechat = student.classes.teacher.users.wechat_id
			msg_title = u'您的学生：%s发起了请假,\n'%student.name
			msg_title += u'开始时间：%s,\n结束时间%s， \n请假原因：%s,\n如同意请回复"ag%s",\n拒绝请回复"re%s",'%(str(ask_start_time),str(ask_end_time),why,ask.id,ask.id)
			wechat.message.send_text(teacher_wechat,msg_title)
		except Exception as e:
			logger.error(u"请假，通知教师错误。微信通知错误"+str(e))

	try:
		teacher_wechat = student.parents.users.wechat_id
		msg_title = u'您的小孩：%s发起了请假,\n'%student.name
		msg_title += u'请假时间：%s至%s \n请假原因：%s'%(str(ask_start_time),str(ask_end_time),why)
		wechat.message.send_text(teacher_wechat,msg_title)
	except Exception as e:
		logger.error(u"请假，通知家长错误。微信通知错误"+str(e))

	
	if ask_state !=1:
		flash(u'请假申请提交成功，请等待班主任(%s)的审核。'%banzhuren.first_name,'success')

	# if current_user.roles==doork:	
	# 	return redirect(url_for('.my_senf_leave'))

	return redirect(url_for('.my_senf_leave'))


#门卫主界面请假
@blueprint.route('/send_leave_json',methods=['POST'])
@csrf_protect.exempt
@login_required
@permission_required(Permission.LEAVE)
def send_leave_json():
	data = json.loads(request.form.get('data'))

	student = Student.query\
		.join(Classes,Classes.id==Student.classesd) \
		.join(Grade,Grade.id==Classes.grades) \
		.join(School,School.id==Grade.school) \
		.filter(School.id==current_user.school)\
		.filter(Student.id==data['student_id'])\
		.first()
	print(data)
	print(student)

	if not student:
		return jsonify({'info':[1,'没有该学生。']})

	if AskLeave.query.filter_by(ask_student=student).filter(AskLeave.charge_state.in_([0,1,4])).first():
		return jsonify({'info':[1,'该请假人已经存在请假申请，不能再次发起申请。']})

	try:
		banzhuren = student.classes.teacher.users
	except Exception as e:
		return jsonify({'info':[1,'该班级未设置班主任。不能请假']})


	ask = AskLeave.create(
		send_ask_user=current_user,
		ask_student = student,
		charge_ask_user = banzhuren,
		ask_start_time = data['start_time'],
		ask_end_time = data['end_time'],
		why = data['note']
	)
	
	#此处增加微信通知班主任和家长
	try:
		teacher_wechat = student.classes.teacher.users.wechat_id
		msg_title = u'您的学生：%s发起了请假,\n'%student.name
		msg_title += u'开始时间：%s,\n结束时间%s， \n请假原因：%s,\n如同意请回复"ag%s",\n拒绝请回复"re%s",'\
			%(str(data['start_time']),str(data['end_time']),data['note'],ask.id,ask.id)
		wechat.message.send_text(teacher_wechat,msg_title)
	except Exception as e:
		logger.error(u"请假，通知教师错误。微信通知错误"+str(e))

	try:
		teacher_wechat = student.parents.users.wechat_id
		msg_title = u'您的小孩：%s发起了请假,\n'%student.name
		msg_title += u'请假时间：%s至%s \n请假原因：%s'%(str(data['start_time']),str(data['end_time']),data['note'])
		wechat.message.send_text(teacher_wechat,msg_title)
	except Exception as e:
		logger.error(u"请假，通知家长错误。微信通知错误"+str(e))


	return jsonify({'info':['请假成功。',student.name,student.classes.name]})
	


#我的请假
@blueprint.route('/my_leave')
@templated()
@login_required
def my_leave():
	if current_user.student:
		askleave = AskLeave.query \
			.join(Student,Student.id==AskLeave.ask_users) \
			.filter(Student.user==current_user.id) \
			.order_by('charge_state').all()
	else:
		askleave  = []
	return dict(askleave=askleave)


@blueprint.route('/charge_leave')
@login_required
@templated()
@permission_required(Permission.ALLOW_LEAVE)
def charge_leave():
	askleave = AskLeave.query.filter_by(charge_ask_user=current_user).order_by('charge_state').all()
	return dict(askleave=askleave)


#我的发起的请假
@blueprint.route('/my_senf_leave')
@login_required
@templated()
def my_senf_leave():
	askleave = AskLeave.query.filter_by(send_ask_user=current_user).order_by('charge_state').all()
	return dict(askleave=askleave)


#同意请假
@blueprint.route('/charge_ask_leave/<int:id>')
@login_required
@permission_required(Permission.ALLOW_LEAVE)
def charge_ask_leave(id=0):
	ask_leave = AskLeave.query.get_or_404(id)
	
	if current_user != ask_leave.charge_ask_user or ask_leave.charge_state!=0:
		flash(u'非法操作','danger')
		return redirect(url_for('public.home'))

	ask_leave.update(charge_state=1,charge_time=dt.datetime.now())
	flash(u'您已同意该请假申请','success')

	return redirect(url_for('user.charge_leave'))
	


#请假归来
@blueprint.route('/return_leave')
@login_required
@templated()
@permission_required(Permission.RETURN_LEAVE)
def return_leave(id=0):
	askleave = AskLeave.query.filter_by(send_ask_user=current_user).filter_by(charge_state=1).order_by('id').all()	
	return dict(askleave=askleave)

@blueprint.route('/change_return_leave/<int:id>')
@login_required
@permission_required(Permission.RETURN_LEAVE)
def change_return_leave(id=0):
	ask_leave = AskLeave.query.get(id)
	if ask_leave:
		if ask_leave.charge_state==1:
			ask_leave.update(charge_state=3,back_leave_time=dt.datetime.now())
			flash(u'请假人已归来，该请假申请已完成','success')
		else:
			flash(u'错误。没有该请假申请，或已完成。','danger')
	else:
		flash(u'错误。没有该请假申请，或已完成。','danger')

	return redirect(url_for('.return_leave'))


#门卫界面
@blueprint.route('/doorkeeper_main')
@templated()
def doorkeeper_main():

	if not current_user.is_authenticated:
		return redirect(url_for('.user_login',next=request.endpoint))

	# ask_leave = AskLeave.query\
	# 	.with_entities(AskLeave,Student)\
	# 	.join(Student,Student.id==AskLeave.ask_users)\
	# 	.filter(AskLeave.send_ask_user==current_user)\
	# 	.filter(AskLeave.charge_state.in_([0,1,4])).all()	
	# ask_leave0 = []
	# ask_leave1 = []
	# ask_leave4 = []
	# for i in ask_leave:
	# 	if i[0].charge_state == 0 :
	# 		ask_leave0.append(i)
	# 	if i[0].charge_state == 1 :
	# 		ask_leave1.append(i)
	# 	if i[0].charge_state == 4 :
	# 		ask_leave4.append(i)


	return dict()


#门卫主页扫描获取学生信息
@blueprint.route('/doorkeeper_main_json')
@templated()
def doorkeeper_main_json():

	if not current_user.is_authenticated:
		return jsonify({'info':[1,'登录失效请刷新']})

	stid = request.args.get('s')
	
	
	stid = stid.split('S')
	if not stid is None:

		try:
			student_id = stid[1]
		except Exception as e:
			return jsonify({'info':[2,'输入错误']})
		
		#
		student = Student.query.get(student_id)

		if not student:
			return jsonify({'info':[2,'错误没有该学生']})

		ask_leave = AskLeave.query.filter_by(ask_student=student).filter(AskLeave.charge_state.in_([0,1,2,4])).first()
		
		#没有请假信息
		if not ask_leave:
			return jsonify({'info':[0,[student.id,student.name,student.img,student.classes.name]]})

		if ask_leave.charge_state == 0:
			return jsonify({'info':[1,'等待班主任确认中。',student.name,student.classes.name]})

		elif ask_leave.charge_state == 1:

			if dt.datetime.now() < ask_leave.ask_start_time:
				return jsonify({'info':[1,'未到请假开始时间',student.name,student.classes.name]})

			ask_leave.update(charge_state=4,leave_time=dt.datetime.now())

			try:
				student_parent_wechat = ask_leave.ask_student.parents.users.wechat_id
				msg_title = '您的小孩已离校，请记得提醒您的小孩在请假结束前(%s)回到学校。'%ask_leave.ask_end_time
				wechat.message.send_text(student_parent_wechat,msg_title)
			except Exception as e:
				logger.error("离校通知家长错误，微信通知错误"+str(e))

			try:
				student_name = student.name
				teacher_wechat = student.classes.teacher.users.wechat_id
				wechat.message.send_text(teacher_wechat,f'您的学生{student_name},请假已离校。')
			except Exception as e:
				logger.error(u"离校，通知教师错误。微信通知错误"+str(e))


			return jsonify({'info':[1,'已同意可离校。',student.name,student.classes.name]})

		if ask_leave.charge_state == 2:
			ask_leave.update(charge_state=3)
			return jsonify({'info':[1,'班主任拒绝该请假',student.name,student.classes.name]})


		elif ask_leave.charge_state == 4:
			ask_leave.update(charge_state=3,back_leave_time=dt.datetime.now())

			try:
				student_parent_wechat = ask_leave.ask_student.parents.users.wechat_id
				if dt.datetime.now() > ask_leave.ask_end_time:
					msg_title = '您的小孩已归校(超出请假结束时间)，请假结束。'
				else:
					msg_title = '您的小孩已归校，请假结束。'
				wechat.message.send_text(student_parent_wechat,msg_title)
			except Exception as e:
				logger.error("归校通知家长错误，微信通知错误"+str(e))

			try:
				student_name = student.name
				ask_leave_time = ask_leave.ask_end_time
				if dt.datetime.now() > ask_leave_time:
					msg_title = f'您的学生 {student_name} 已归校(超出请假结束时间[{ask_leave_time}])，销假完成。'
				else:
					msg_title = f'您的学生{student_name}，请假已回校。销假完成'
				teacher_wechat = student.classes.teacher.users.wechat_id
				wechat.message.send_text(teacher_wechat,msg_title)
			except Exception as e:
				logger.error(u"归校，通知教师错误。微信通知错误"+str(e))

			if dt.datetime.now() > ask_leave.ask_end_time:
				return jsonify({'info':[1,'已归来超出时间',student.name,student.classes.name]})
			else:
				return jsonify({'info':[1,'已归来请假完成',student.name,student.classes.name]})

		return jsonify({'info':[0,[student.id,student.name]]})

	return jsonify({'info':[2,'输入错误']})



@blueprint.route('/user_login')
@templated()
def user_login():
	return dict(next=request.args.get('next'))

@blueprint.route('/user_login',methods=['POST'])
def user_login_post():
	username = request.form.get('username','0')
	password = request.form.get('password','0')
	user = User.query.filter_by(username=username).first()
	
	if user and  user.check_password(password):
		login_user(user,True)
		return redirect(url_for(request.args.get('next')) or url_for('public.home'))
	else:
		flash('信息输入错误，没有该用户。')
		return redirect(url_for('.user_login'))


#自动注册 
@blueprint.route('/autoregister')
@oauth(scope='snsapi_base')
def autoregister():

	wechat_id = session.get('wechat_user_id','')
	
	if wechat_id:
		user = User.query.filter_by(wechat_id=session.get('wechat_user_id')).first()
	else:
		user = []
	if user:
		login_user(user,True)
		return redirect(request.args.get('next') or url_for('public.home'))


	choice_str = 'ABCDEFGHJKLNMPQRSTUVWSXYZ'
	username_str = ''
	password_str = ''
	str_time =  time.time()
	username_str = 'AU'
	username_str += str(int(int(str_time)*1.301))
	for i in range(2):
		username_str += random.choice(choice_str)

	for i in range(6):
		password_str += random.choice(choice_str)

	username = username_str
	password = password_str

	user = User.query.filter_by(username=username).first()
	if user is None:
		user = User.create(
			username=username,
			password=password,
			wechat_id=wechat_id,
		)
		login_user(user,True)
		return redirect(request.args.get('next') or url_for('public.home'))
	else:
		return redirect(url_for('.autoregister'))


@blueprint.route('/autologin/<string:name>')
def autologin(name=''):
	login_user(User.query.filter_by(username=name).first())
	return redirect(url_for('public.home'))



