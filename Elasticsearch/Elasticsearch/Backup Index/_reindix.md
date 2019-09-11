```json
POST _reindix
{
    "source": {
        "index": "xxxxx-*"
    },
    "dest":{
        "index": "xxxxx-new"
    }
}
```
#### Example
```json
POST _reindex
{
  "source": {
    "index": "twitter",
    "type": "user"
  },
  "dest": {
    "index": "users",
    "type": "_doc"
  }
}


POST _reindex
{
  "source": {
    "index": "twitter"
  },
  "dest": {
    "index": "new_twitter"
  },
  "script": {
    "source": """
      ctx._source.type = ctx._type;
      ctx._id = ctx._type + '-' + ctx._id;
      ctx._type = '_doc';
    """
  }
}
```