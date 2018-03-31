#coding=utf-8
from flask_wechatpy import wechat_required,menu
from wechatpy.replies import TextReply
from flask import request,current_app


from . import wechat

def createmenu():
    menu.create({"button":[
        {"type":"view","name":u"我要找货","sub_button":[
            {
                "type":"view",
                "name":u"我发布的车",
                "url":'http://car.anaf.cn/usercenter/show_order'
            },
            {
                "type":"view",
                "name":u"发布车信息",
                "url":'http://car.anaf.cn/driver/add_post'
            },
            {
                "type":"view",
                "name":u"货物列表",
                "url":'http://car.anaf.cn/consignor'
            },
            ]},\
        {"type":"view","name":u"我要找车","sub_button":[
        {
                "type":"view",
                "name":u"我发布的货",
                "url":'http://car.anaf.cn/usercenter/show_order'
            },
            {
                "type":"view",
                "name":u"发布货信息",
                "url":'http://car.anaf.cn/consignor/send_goods'
            },
            {
                "type":"view",
                "name":u"车辆列表",
                "url":'http://car.anaf.cn/driver'
            },
            ]},\
        {"type":"view","name":u"我的服务","sub_button":[
        {
                "type":"view",
                "name":u"平台简介",
                "url":'https://s.wcd.im/v/2efu6Z37/'
            },
            {
                "type":"click",
                "name":u"联系方式",
                "key":'contact_us'
            },
            {
                "type":"view",
                "name":u"个人中心",
                "url":'http://car.anaf.cn/usercenter'
            },
            ]},\
        ]})



#微信获取token
@wechat.route('/token',methods=['GET'])
@wechat_required
def get_token():
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
@wechat.route('/token',methods=['POST'])
@wechat_required
def post_post():
	msg = request.wechat_msg
    reply = TextReply(content='欢迎关注', message=msg)
    return reply
    




