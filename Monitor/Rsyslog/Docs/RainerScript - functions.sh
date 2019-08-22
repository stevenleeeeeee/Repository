#RainerScript支持当前非常有限的一组函数：

getenv(str)
#与OS调用一样，返回环境变量的值(如果存在)，若不存在则返回空字符串
#以下示例可用于基于某些环境变量构建动态过滤器：
if $msg contains getenv('TRIGGERVAR') then /path/to/errfile

strlen(str)
#返回提供的字符串的长度
tolower(str)
#将提供的字符串转换为小写

cstr(expr)
#将expr转换为字符串值
cnum(expr)
#将expr转换为数字(整数)注意：如果表达式不包含数值，则行为未定义。

wrap(str，wrapper_str)
返回用wrapper_str包装的str
#例如：wrap("foo bar","##") 输出：---> "##foo bar##"

replace(str，substr_to_replace，replace_with)
#返回新字符串，其中substr_to_replace的所有实例都替换为replace_with。
例如：replace("foo bar baz"," b",",B") 输出: ---> "foo，Bar，Baz"

re_match(expr，re)
#返回1，如果expr匹配re，则返回0。使用POSIX ERE

re_extract(expr，re，match，submatch，no-found)
#通过正则表达式匹配从字符串(属性)中提取数据。使用POSIX ERE正则表达式。
#变量"match"包含要使用的匹配数。这允许拾取超过第一个表达式匹配。
#子匹配是要匹配的子匹配(支持最多50个)。
#"no-found"参数指定在未找到正则表达式时要返回的字符串。请注意，匹配和子匹配从零开始。目前无法通过一次调用提取多个子匹配。


field(str，delim，matchnbr)
#返回基于字段的子字符串。str是要搜索的字符串，delim是分隔符，matchnbr是要搜索的匹配项 (第一个匹配从1开始)。
#这与基于字段的属性 - 替换选项类似。7.3.7之前的版本仅支持单个字符作为分隔符。
#从7.3.7版开始，可以使用完整字符串作为分隔符。
#如果将单个字符用作分隔符，则delim是字段分隔符字符的数字ascii值(以便可以指定不可打印的字符)。如果字符串用作分隔符，则指定多字符串(例如“＃011”)。
#请注意，当将单个字符指定为字符串时 ，将完成基于字符串的提取，这比等效的单字符提取更具性能 。例如。field($msg,",",3)field($msg,44 ,3)

set $!usr!field = field($msg,32,3);  -- the third field,delimited by space
set $!usr!field = field($msg,"#011",2); -- the second field,delimited by "#011"

exec_template
#通过执行模板设置变量。基本上，这允许容易地提取属性的某些部分并且稍后将其用作任何其他变量。
template(name="extract" type="string" string="%msg:F:5%")
set $!xyz = exec_template("extract");
#the variable xyz can now be used to apply some filtering :
if $!xyz contains 'abc' then {action()}
#or to build dynamically a file path :
template(name="DynaFile" type="string" string="/var/log/%$!xyz%-data/%timereported%-%$!xyz%.log")

ltrim
#删除给定字符串开头的任何空格。Input是一个字符串，output是从第一个非空格字符开始的相同字符串。
rtrim 
#删除给定字符串末尾的任何空格。Input是一个字符串，output是与最后一个非空格字符结尾的相同字符串。

substring(str,start,subStringLength)
#从str创建子字符串。子字符串从start开始，最多为subStringLength个字符。


#Example:  (从消息中获取内容赋值给变量)
set $.befortime = re.extract($!push!f1, "([0-2][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9])([0-9][0-9]:[0-9][0-9]:[0-9][0-9])",0,1,"");
set $.aftertime = re.extract($!push!f1, "([0-2][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9])([0-9][0-9]:[0-9][0-9]:[0-9][0-9])",0,2,"");
set $!push!ldatetime = $.befortime & "T" & $.aftertime & "+0800";
#这里使用了 re_extract 函数来通过正则匹配日志中的内容