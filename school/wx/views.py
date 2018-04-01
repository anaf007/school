#coding=utf-8
from flask import Blueprint, render_template, url_for, current_app, redirect,request,flash
from flask_wechatpy import wechat_required
from wechatpy.replies import TextReply,ArticlesReply,create_reply,ImageReply
# from school.extensions import wechat


blueprint = Blueprint('wx', __name__, url_prefix='/wx')


#微信获取token
@blueprint.route('/token',methods=['GET'])
@wechat_required
def token_get():
    signature = request.args.get('signature','')
    timestamp = request.args.get('timestamp','')
    nonce = request.args.get('nonce','')
    echostr = request.args.get('echostr','')
    token = current_app.config['SCHOOL_WECHAT_TOKEN']
    sortlist = [token, timestamp, nonce]
    sortlist.sort()
    sha1 = hashlib.sha1()
    map(sha1.update, sortlist)
    hashcode = sha1.hexdigest()
    try:
        check_signature(token, signature, timestamp, nonce)
    except InvalidSignatureException:
        abort(403)
    return echostr



#微信调用 位置和token等其他相关
@blueprint.route('/token',methods=['POST'])
@wechat_required
def token_post():
    msg = request.wechat_msg
    with open('/tmp/error.log', 'w') as f:
        f.write('33')

    reply  = ''

     if msg.event == 'subscribe':
        reply = TextReply(content='欢迎关注调..', message=msg)
        #创建菜单
        # createmenu()


    try:
        
        reply = TextReply(content='hhhhh', message=msg)
        with open('/tmp/error.log', 'w') as f:
            f.write('222')
        return reply
    except Exception, e:
        with open('/tmp/error.log', 'w') as f:
            f.write('111')
        return str(e)

    return reply
    





