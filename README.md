Evernote Export to Hexo Note
============================================

Overview
---
Already contains Evernote Python3 SDK  V1.25.
Just input param in `config.json` and run 
`python ExportEverNoteBlog.py`

Config Demo
---
```json
{
  "EvernoteToken": "S=s6:U=6.....",
  "NoteStoreUrl": "https://www.evernote.com/shard/s11/notestore",
  "EverNoteRootNotebook": "Blog",
  "ExportHTMLPath": "D:/cygwin/home/geosmart.io/source/_posts",
  "CandidateNoteBookName": "Z00Candidate"
}
```

Prerequisites
---
1. Python 3 installed
2. get evernote develop token in [DeveloperToken](https://www.evernote.com/api/DeveloperToken.action)

3. `pip install bs4`
4. hexo config
5. hexo blog deploy
