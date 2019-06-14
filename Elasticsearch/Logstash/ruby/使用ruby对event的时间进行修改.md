```ruby
        ruby{
            code => 'event.set("time",(Time.parse(event.get("log_time"))))'
       }
        ruby{
            code => 'event.set("time",event.get("time")+8*60*60)'
        }
```