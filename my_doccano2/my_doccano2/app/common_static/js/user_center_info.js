var vm = new Vue({
    el: '#app',
    data: {
        host,
        user_id: sessionStorage.user_id || localStorage.user_id,
        token: sessionStorage.token || localStorage.token,
        username: '',
        mobile: '',
        email: '',
        email_active: false,
        set_email: false,
        send_email_btn_disabled: false,
        send_email_tip: '重新发送验证邮件',
        email_error: false,
//        histories: []
        projects:[]
    },
    mounted: function(){
        // 判断用户的登录状态
        if (this.user_id && this.token) {
            axios.get(this.host + "/users/"+this.user_id, {
                    // 向后端传递JWT token的方法
                    headers: {
                        'Authorization': 'JWT ' + this.token
                    },
                    responseType: 'json',
                })

                .then(response => {
                    // 加载用户数据
                    this.user_id = response.data.data.id;
                    this.username = response.data.data.username;
                    this.mobile = response.data.data.mobile;
//                    this.email = response.data.data.email;
//                    this.email_active = response.data.data.email_active;

                    // 补充请求浏览历史
                    axios.get(this.host + '/projects/', {
                            headers: {
                                'Authorization': 'JWT ' + this.token
                            },
                            responseType: 'json'
                        })
                        .then(response => {
                            this.projects = response.data.data.results;
                            alert("projects")
                            alert(response.data.data.results)
                            for(var i=0; i<this.projects.length; i++){
                                this.projects[i].url = '/projects/' + this.projects[i].id + '.html';
                            }
                        })
//
                })
                .catch(error => {
                    alert("错误")
                    if (error.response.status==401 || error.response.status==403) {
                        location.href = '/login.html?next=/user_center_info.html';
                    }
                });
        } else {
            location.href = '/login.html?next=/user_center_info.html';
        }
    },
    methods: {
        // 退出
        logout: function(){
            sessionStorage.clear();
            localStorage.clear();
            location.href = '/login.html';
        },
        // 保存email
        save_email: function(){
            var re = /^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$/;
            if(re.test(this.email)) {
                this.email_error = false;
            } else {
                this.email_error = true;
                return;
            }
            axios.put(this.host + '/email/',
                { email: this.email },
                {
                    headers: {
                        'Authorization': 'JWT ' + this.token
                    },
                    responseType: 'json'
                })
                .then(response => {
                    this.set_email = false;
                    this.send_email_btn_disabled = true;
                    this.send_email_tip = '已发送验证邮件'
                })
                .catch(error => {
                    alert(error.data);
                });
        }
    }
});