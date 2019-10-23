// 执行groovy脚本： groovy test.groovy

// 打印
println 'hello'
// 或：
def name = '张三'
println "hello $name"

// 打印cmd命令执行后的结果，在groovy中只要把字符串后面调用execute方法就能执行字符串中的命令
println 'cmd /c dir'.execute().text

// 在进程处理中有时需要等待进程执行完成之后才能进行下面的操作：
def proc = 'cmd /c dir'.execute()
proc.waitFor()
println proc.text

// 上面waitFor函数是永久等待，如果想要等待一段时间： （毫秒为单位）
proc.waitForOrKill(1000)

// Groovy 定义变量的方式和 Java 是类似的
// 区别在于 Groovy 提供了def关键字供使用，它可以省略变量类型的定义，根据变量的值进行类型推导。



// 判断
class Example { 
   static void main(String[] args) { 
      // Initializing a local variable 
      int a = 2 
		
      //Check for the boolean condition 
      if (a<100) { 
         //If the condition is true print the following statement 
         println("The value is less than 100"); 
      } 
   } 
}