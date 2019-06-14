```ruby
 ruby {
	code => "
            file = File.open('/etc/logstash/config/filter-whilelist.txt', 'r')
            text = file.read
            file.close
			event.cancel if !text.include?(event.project)
		    "
}
```