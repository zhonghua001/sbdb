
function change_group(flag,selected_group,selected_host){

    var host_group = selected_group;
    if (flag == -1){
         host_group = $("#id_select_group option:selected").val();
    }

    var select_host = $("#select_host");
    $(select_host).empty();
    $(select_host).append('<option  id="select_host" value ="" selected disabled >---Select Host---</option>');

    $.ajax({url:'/dbmanage/get_host/',
            data:{'host_group':host_group},
            success:function(ret){
               $.each(JSON.parse(ret).host_list,function(key,value) {
                   var not_instance_ip = '';
                   if (selected_group == '0' || flag == -1){

                         var v = '';
                        for ( var i in value){for (var acc in  value[i]) {
                               v +='['+value[i][acc]+']';
                              // console.log(i,value[i][acc])
                           }}

                           if (key<0){ not_instance_ip = i;}else{not_instance_ip=key;}
                           if (v === '[,]'){
                               if (key<0){

                                    $("#select_host").append('<option value="'+not_instance_ip+'">'+i+' 无实例，请先创建</option>')
                               }else{

                               $("#select_host").append('<option value="'+not_instance_ip+'">'+i+' 无账号</option>')
                               }

                           }
                           else{  $("#select_host").append('<option value="' + not_instance_ip + '">' + i + ' 已有账号列表:' + v + '</option>')}

                       }

                   else {
                       var select_flag='';

                      var v = '';
                        for ( var i in value){for (var acc in  value[i]) {
                               v +='['+value[i][acc]+']';
                              // console.log(i,value[i][acc])
                           }}
                       if (key<0){ not_instance_ip = i;}else{ not_instance_ip=key;}
                       if (selected_host == not_instance_ip){
                           select_flag='selected="selected"';

                           if (v == '[,]'){
                                  if (key<0){
                                  $("#select_host").append('<option '+select_flag+' value="'+not_instance_ip+'">'+i+'无实例，请先创建</option>')
                                  }
                                  else{

                                      $("#select_host").append('<option '+select_flag+' value="'+not_instance_ip+'">'+i+'无账号</option>')
                                  }
                           }
                           else{
                                  $("#select_host").append('<option '+select_flag+' value="' + not_instance_ip + '">' + i + ' 已有账号列表:' + v + '</option>')
                           }
                         }
                         else{
                              if(v == '[,]'){
                                   if (key<0){
                                       $("#select_host").append('<option '+select_flag+' value="'+not_instance_ip+'">'+i+'无实例，请先创建</option>')
                                   }
                                   else{
                                    $("#select_host").append('<option '+select_flag+' value="'+not_instance_ip+'">'+i+'无账号</option>')
                                   }

                              }
                               else{
                                  $("#select_host").append('<option '+select_flag+' value="' + not_instance_ip + '">' + i + ' 已有账号列表:' + v + '</option>')
                              }

                         }

                   }
                }
               )
        }
    })
}




function change_group_db_user(flag,selected_group,selected_host){

    var host_group = selected_group;
    if (flag == -1){
         host_group = $("#id_select_group_db_user option:selected").val();
    }

    var select_host = $("#select_host_db_user");
    $(select_host).empty();
    $(select_host).append('<option  id="select_host" value ="" selected disabled >---Select Host---</option>');

    $.ajax({url:'/dbmanage/get_host/',
            data:{'host_group':host_group},
            success:function(ret){
               $.each(JSON.parse(ret).host_list,function(key,value) {
                   var not_instance_ip = '';
                   if (selected_group == '0' || flag == -1){

                       var v = '';
                        for ( var i in value){for (var acc in  value[i]) {
                               v +='['+value[i][acc]+']';
                              // console.log(i,value[i][acc])
                           }}

                           if (key<0){ not_instance_ip = i;}else{not_instance_ip=key;}
                           if (v === '[,]'){
                               if (key<0){

                                    $("#select_host_db_user").append('<option disabled value="'+not_instance_ip+'">'+i+' 无实例，请先创建</option>')
                               }else{

                               $("#select_host_db_user").append('<option disabled value="'+not_instance_ip+'">'+i+' 无账号</option>')
                               }

                           }
                           else{  $("#select_host_db_user").append('<option value="' + not_instance_ip + '">' + i + ' 已有账号列表:' + v + '</option>')}

                       }

                   else {
                       var select_flag='';

                       var v = '';
                        for ( var i in value){for (var acc in  value[i]) {
                               v +='['+value[i][acc]+']';
                              // console.log(i,value[i][acc])
                           }}
                       if (key<0){ not_instance_ip = i;}else{ not_instance_ip=key;}
                       if (selected_host == not_instance_ip){
                           select_flag='selected="selected"';

                           if (v == '[,]'){
                                  if (key<0){
                                  $("#select_host_db_user").append('<option disabled'+select_flag+' value="'+not_instance_ip+'">'+i+'无实例，请先创建</option>')
                                  }
                                  else{

                                      $("#select_host_db_user").append('<option disabled'+select_flag+' value="'+not_instance_ip+'">'+i+'无账号</option>')
                                  }
                           }
                           else{
                                  $("#select_host_db_user").append('<option '+select_flag+' value="' + not_instance_ip + '">' + i + ' 已有账号列表:' + v + '</option>')
                           }
                         }
                         else{
                              if(v == '[,]'){
                                   if (key<0){
                                       $("#select_host_db_user").append('<option disabled'+select_flag+' value="'+not_instance_ip+'">'+i+'无实例，请先创建</option>')
                                   }
                                   else{
                                    $("#select_host_db_user").append('<option disabled'+select_flag+' value="'+not_instance_ip+'">'+i+'无账号</option>')
                                   }

                              }
                               else{
                                  $("#select_host_db_user").append('<option '+select_flag+' value="' + not_instance_ip + '">' + i + ' 已有账号列表:' + v + '</option>')
                              }

                         }

                   }
                }
               )
        }
    })
}




function change_group_sysaccount(flag,selected_group,selected_host){

    var host_group = selected_group;
    if (flag == -1){
         host_group = $("#id_select_group_sysaccount option:selected").val();
    }

    var select_host = $("#select_host_sysaccount");
    $(select_host).empty();
    $(select_host).append('<option  id="select_host" value ="" selected disabled >---Select Host---</option>');

    $.ajax({url:'/dbmanage/get_host/',
            data:{'host_group':host_group},
            success:function(ret){
               $.each(JSON.parse(ret).host_list,function(key,value) {
                   var not_instance_ip = '';
                   if (selected_group == '0' || flag == -1){

                           var v = '';
                           for ( var i in value){for (var acc in  value[i]) {
                               v +='['+value[i][acc]+']';
                              // console.log(i,value[i][acc])
                           }
                           }


                           if (key<0){ not_instance_ip = i;}else{not_instance_ip=key;}
                           if (v === '[,]'){
                               if (key<0){

                                    $("#select_host_sysaccount").append('<option disabled value="'+not_instance_ip+'">'+i+' 无实例，请先创建</option>')
                               }else{

                               $("#select_host_sysaccount").append('<option disabled value="'+not_instance_ip+'">'+i+' 无账号</option>')
                               }

                           }
                           else{  $("#select_host_sysaccount").append('<option value="' + not_instance_ip + '">' + i + ' 已有账号列表:' + v + '</option>')}

                       }

                   else {
                       var select_flag='';
                       console.log(value);
                       var v = '';
                        for ( var i in value) {
                            for (var acc in  value[i]) {
                                v += '[' + value[i][acc] + ']';
                                // console.log(i,value[i][acc])
                            }
                        }
                       if (key<0){ not_instance_ip = i;}else{ not_instance_ip=key;}
                       if (selected_host == not_instance_ip){
                           select_flag='selected="selected"';

                           if (v == '[,]'){
                                  if (key<0){
                                  $("#select_host_sysaccount").append('<option disabled'+select_flag+' value="'+not_instance_ip+'">'+i+'无实例，请先创建</option>')
                                  }
                                  else{

                                      $("#select_host_sysaccount").append('<option disabled'+select_flag+' value="'+not_instance_ip+'">'+i+'无账号</option>')
                                  }
                           }
                           else{
                                  $("#select_host_sysaccount").append('<option '+select_flag+' value="' + not_instance_ip + '">' + i + ' 已有账号列表:' + v + '</option>')
                           }
                         }
                         else{
                              if(v == '[,]'){
                                   if (key<0){
                                       $("#select_host_sysaccount").append('<option disabled'+select_flag+' value="'+not_instance_ip+'">'+i+'无实例，请先创建</option>')
                                   }
                                   else{
                                    $("#select_host_sysaccount").append('<option disabled'+select_flag+' value="'+not_instance_ip+'">'+i+'无账号</option>')
                                   }

                              }
                               else{
                                  $("#select_host_sysaccount").append('<option '+select_flag+' value="' + not_instance_ip + '">' + i + ' 已有账号列表:' + v + '</option>')
                              }

                         }

                   }
                }
               )
        }
    })
}