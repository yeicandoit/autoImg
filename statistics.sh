mysqlcmd="mysql -uminisite -pb8c1038bb29baf5b4f6043c51c259fae -h10.4.11.22 mini_site -e "
declare -A dic
dic=(["batterydoctor"]="金山电池医生" ["calendar"]="万年历" ["esbook"]="宜搜小说" ["hers"]="她社区" ["jxedt"]="驾校一点通" ["meiyancamera"]="美颜相机" ["qiushi"]="糗事百科" ["qnews"]="腾讯新闻" ["QQBrowser"]="QQ浏览器" ["shuqi"]="书旗小说" ["tianya"]="天涯论坛" ["wantu"]="玩图" ["weixin"]="微信" ["banner"]="横幅" ["kai"]="开屏" ["feeds"]="信息流" ["cha"]="插屏" ["feeds_banner"]="评论页横幅" ["feeds_big"]="信息流大图" ["feeds_multi"]="信息流组图" ["feeds_small"]="信息流小图" ["image_text"]="图文" ["fine_big"]="优雅大图" ["QQWeather"]="QQ天气" ["QQDongtai"]="QQ动态")

sDate=$1

##########Print total###########
total=`$mysqlcmd "select count(*) from autoimage where reqDate >= \"$sDate\""`
total=`echo $total|awk '{print $2}'`
echo "上周自动P图情况如下，"
echo -e "总数\t$total"

##########Print num for every user##########
userinfo=`$mysqlcmd "select count(*), email from autoimage where reqDate >= \"$sDate\" group by email"`
userinfoArr=($userinfo)
echo -e "\n各个运营同学P图数量如下,"
for((i=2; i<${#userinfoArr[@]}; i=i+2))
do
    name=`echo ${userinfoArr[i+1]} | awk -F'@' '{print $1}'`
    echo -e "$name:\t\t${userinfoArr[i]}"
done

##########Print num for every position##########
androidinfo=`$mysqlcmd "select count(*), app, adType from autoimage where reqDate >= \"$sDate\" and os=\"android\" group by app, adType"`
androidinfoArr=($androidinfo)
echo -e "\nandroid各个点位P图数量如下,"
for((i=3; i<${#androidinfoArr[@]};i=i+3))
do
    if !([ "${androidinfoArr[i]}" -gt 0 ] 2>/dev/null)
    then
	((i=i-1))
    fi
    echo -e "${dic[${androidinfoArr[i+1]}]}${dic[${androidinfoArr[i+2]}]}:\t${androidinfoArr[i]}"
done

iosinfo=`$mysqlcmd "select count(*), app, adType from autoimage where reqDate >= \"$sDate\" and os=\"ios\" group by app, adType"`
iosinfoArr=($iosinfo)
echo -e "\nios各个点位P图数量如下,"
for((i=3; i<${#iosinfoArr[@]};i=i+3))
do
    if !([ "${iosinfoArr[i]}" -gt 0 ] 2>/dev/null)
    then
	((i=i-1))
    fi
    echo -e "${dic[${iosinfoArr[i+1]}]}${dic[${iosinfoArr[i+2]}]}:\t${iosinfoArr[i]}"
done
