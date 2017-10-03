#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os

package_file = os.path.normpath(os.path.abspath(__file__))
package_path = os.path.dirname(package_file)
lib_path = os.path.join(package_path, "lib")

evernote_path = os.path.join(package_path, "lib", "evernote-sdk-python3", "lib")

if lib_path not in sys.path:
    sys.path.append(lib_path)
if evernote_path not in sys.path:
    sys.path.append(evernote_path)

import evernote.edam.userstore.UserStore as UserStore
import evernote.edam.notestore.NoteStore as NoteStore
import thrift.protocol.TBinaryProtocol as TBinaryProtocol
import thrift.transport.THttpClient as THttpClient

import webbrowser


def LOG(*args):
    print("Evernote: ", *args)


class BlogExporter:
    """
    export evernote notes to static blog
    """
    _exportHTMLPath = None
    _everNoteRootNotebook = None
    _everNoteClient = None
    _noteStore = None
    _notebooks = None

    def __init__(self, everNoteClient, exportHtmlPath, everNoteRootNotebook):
        self._everNoteRootNotebook = everNoteRootNotebook
        self._exportHTMLPath = exportHtmlPath
        self._everNoteClient = everNoteClient

    def export_blog(self):
        self._noteStore = self._everNoteClient.get_note_store()
        self._notebooks = self._everNoteClient.get_notebooks()

        notebooks = [x for x in self._notebooks if x.stack == self._everNoteRootNotebook]
        # TODO tunning:concurrent
        for notebook in notebooks:
            notes = self._everNoteClient.find_notes_metadata(notebook.guid)
            for note_meta in notes:
                # notes.reverse()
                LOG("Retrieving note \"%s\"..." % note_meta.title)
                self.render_note(notebook, note_meta)

    def render_note(self, notebook, note_meta):
        try:
            note = self._everNoteClient.get_note(note_meta.guid)
            noteCreateDate = self._everNoteClient.get_note_creation_date(note.created)
            noteTagName = self._everNoteClient.get_note_tag_name(note.guid)
            noteHeader = self.render_hexo_blog_metadata(notebook.name, note.title, noteCreateDate, noteTagName)
            notePath = self._exportHTMLPath + '/' + self.get_note_path(noteCreateDate, note.title)
            soup = self.parse_note_resource(note, notePath)

            f = open(notePath + '.html', mode="w", encoding='utf-8')
            f.write(noteHeader + soup)
            f.close()
            LOG("Conversion ok")
        except:
            LOG("Conversion failed")
            raise

    def parse_note_resource(self, note, notePath):
        # from html2text import html2text
        # html convert to markdown
        # mdtxt = html2text(note.content)
        from bs4 import BeautifulSoup
        from bs4 import Tag
        soup = BeautifulSoup(note.content, "html.parser")
        # TODO tunning:concurrent
        # TODO tunning:without downloading existed resource
        # <en-media longdesc = "./1506490529273.png" alt="demo" title="" type ="image/png" hash= "ddf6a5a3693ad0d4cd5b33dbd60c7203"  style = "border: 0; vertical-align: middle; max-width: 100%;" / >
        for enMedia in soup.findAll('en-media'):
            longdesc = enMedia.get("longdesc")
            imgAlt = enMedia.get("alt")
            imgType = enMedia.get("type")
            hash = enMedia.get("hash")
            imgPath = self.download_note_resource(notePath, note.guid, imgAlt, imgType, hash)
            imgTag = soup.new_tag('img', src=imgPath, alt=imgAlt)
            index = enMedia.parent.contents.index(enMedia)
            enMedia.parent.insert(index + 1, imgTag)
        return str(soup)

    def render_hexo_blog_metadata(self, noteBookName, noteName, noteCreateDate, noteTags):
        """
        ---
        title: TensorFlow
        date: 2017-07-01 11:46:21
        tags: [TensorFlow,Python,Anaconda,Jupyter]
        categories: AI
        ---
        Returns:string
        """
        meta = "---\n"
        meta += "title: %s\n" % (noteName or "Untitled")
        meta += "date: %s\n" % noteCreateDate
        meta += "tags: [%s]\n" % (",".join(noteTags))
        meta += "categories: %s\n" % noteBookName
        meta += "---\n\n"
        return meta

    def download_note_resource(self, notePath, noteGuid, resName, mimeType, resHash):
        """
        download image and save to local path
        Args:
            noteGuid: note guid
            hash: note resource hash code

        Returns: image relative path
        """
        import codecs
        hash_bin = codecs.decode(resHash, 'hex')
        try:
            resName = resHash if (resName is None) else resName
            resource = self._everNoteClient.get_resource_by_hash(hash_bin, noteGuid)
            return self.save(notePath, resName, mimeType, resource.data.body)
        except:
            raise

    def save(self, notePath, fileName, mimeType, data):
        """
        save the specified hash and return the saved file's URL
        """
        MIME_TO_EXTESION_MAPPING = {
            'image/png': '.png',
            'image/jpg': '.jpg',
            'image/jpeg': '.jpg',
            'image/gif': '.gif'
        }
        print('download note  %s resource-%s' % (notePath, fileName))
        if not os.path.exists(notePath):
            os.makedirs(notePath)

        if fileName is not None:
            # eg: 2017/09/noteName/imagename.jpg
            noteRes = notePath + '/' + fileName + MIME_TO_EXTESION_MAPPING[mimeType]
            f = open(noteRes, "wb")
            f.write(data)
            f.close()

            return fileName + MIME_TO_EXTESION_MAPPING[mimeType]

        else:
            return ""

    def get_note_path(self, noteCreateDate, noteName):
        return noteCreateDate.split("-")[0] + '/' + noteCreateDate.split("-")[1] + '/' + noteName


class EverNoteClient:
    """
    evernote client
    """
    _token = None
    _noteStoreUrl = None
    _noteStore = None
    _notebooks = None
    settings = None

    def __init__(self, token, noteStoreUrl):
        self._token = token
        self._noteStoreUrl = noteStoreUrl
        if self._token:
            if not self._noteStoreUrl:
                self._noteStoreUrl = self.derive_note_store_url()
            LOG("token param {0}".format(self._token))
            LOG("url param {0}".format(self._noteStoreUrl))
        else:
            webbrowser.open_new_tab("https://www.evernote.com/api/DeveloperToken.action")

    def derive_note_store_url(self):
        token_parts = self._token.split(":")
        id = token_parts[0][2:]
        url = "http://www.evernote.com/shard/" + id + "/notestore"
        return url

    def get_resource_by_hash(self, hashBin, noteGuid):
        resource = self._noteStore.getResourceByHash(self._token, noteGuid, hashBin, True, False,
                                                     False)
        return resource

    def find_notes_metadata(self, notebookGuid):
        notes = self._noteStore.findNotesMetadata(self._token, NoteStore.NoteFilter(notebookGuid=notebookGuid), 0,
                                                  1000,
                                                  NoteStore.NotesMetadataResultSpec(includeTitle=True,
                                                                                    includeAttributes=True)
                                                  ).notes
        return notes

    def get_note_store(self):
        if EverNoteClient._noteStore:
            return EverNoteClient._noteStore
        noteStoreUrl = "https://www.evernote.com/shard/s56/notestore"
        LOG("I've got this for noteStoreUrl -->{0}<--".format(noteStoreUrl))
        LOG("I've got this for token -->{0}<--".format(self._token))
        noteStoreHttpClient = THttpClient.THttpClient(noteStoreUrl)
        USER_AGENT = {'User-Agent': 'Hexo Blog'}
        noteStoreHttpClient.setCustomHeaders(USER_AGENT)
        noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)
        noteStore = NoteStore.Client(noteStoreProtocol)
        print('There are {} notebooks in your account'.format(len(noteStore.listNotebooks(self._token))))

        EverNoteClient._noteStore = noteStore
        return noteStore

    def get_notebooks(self):
        if EverNoteClient._notebooks:
            LOG("Using cached notebooks list")
            return EverNoteClient._notebooks
        notebooks = None
        try:
            noteStore = self.get_note_store()
            notebooks = noteStore.listNotebooks(self._token)
            LOG("Fetched all notebooks!")
        except Exception as e:
            LOG(e)
            # sublime.error_message('Error getting notebooks: %s' % e)
        EverNoteClient._notebooks = notebooks
        return notebooks

    def get_note(self, noteGuid):
        return self._noteStore.getNote(self._token, noteGuid, True, False, False, False)

    def get_note_tag_name(self, tagGuid):
        return self._noteStore.getNoteTagNames(self._token, tagGuid)

    def get_note_creation_date(self, noteCreateDate):
        import datetime
        return datetime.datetime.fromtimestamp(int(noteCreateDate / 1000)).strftime('%Y-%m-%d')
        # return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':
    import json

    with open('config.json') as config_file:
        config = json.load(config_file)
        EvernoteToken = config['EvernoteToken']
        EverNoteRootNotebook = config['EverNoteRootNotebook']
        NoteStoreUrl = config['NoteStoreUrl']
        ExportHTMLPath = config['ExportHTMLPath']

        everNoteClient = EverNoteClient(EvernoteToken, NoteStoreUrl)
        cmd = BlogExporter(everNoteClient, ExportHTMLPath, EverNoteRootNotebook)
        cmd.export_blog()
