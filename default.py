# *  Credits:
# *
# *  original Artist Slideshow Helper code by pkscuot
# *

import xbmc, xbmcaddon, xbmcvfs
import ntpath, os, sys, unicodedata
if sys.version_info >= (2, 7):
    import json
    from collections import OrderedDict
else:
    from resources.ordereddict.OrderedDict import OrderedDict
    import simplejson as json

__addon__        = xbmcaddon.Addon()
__addonname__    = __addon__.getAddonInfo('id')
__addonversion__ = __addon__.getAddonInfo('version')
__addonpath__    = __addon__.getAddonInfo('path').decode('utf-8')
__addonicon__    = xbmc.translatePath('%s/icon.png' % __addonpath__ )
__language__     = __addon__.getLocalizedString


def log(msg, level=xbmc.LOGDEBUG):
    plugin = "Artist Slideshow Helper"
    if type(msg).__name__=='unicode':
        msg = msg.encode('utf-8')
    xbmc.log("[%s] %s" % (plugin, msg.__str__()), level)

def checkDir(path):
    if not xbmcvfs.exists(path):
        xbmcvfs.mkdir(path)

def getCacheThumbName(url, CachePath):
    thumb = xbmc.getCacheThumbName(url)
    thumbpath = os.path.join(CachePath, thumb.encode('utf-8'))
    return thumbpath

def smartUnicode(s):
    if not s:
        return ''
    try:
        if not isinstance(s, basestring):
            if hasattr(s, '__unicode__'):
                s = unicode(s)
            else:
                s = unicode(str(s), 'UTF-8')
        elif not isinstance(s, unicode):
            s = unicode(s, 'UTF-8')
    except:
        if not isinstance(s, basestring):
            if hasattr(s, '__unicode__'):
                s = unicode(s)
            else:
                s = unicode(str(s), 'ISO-8859-1')
        elif not isinstance(s, unicode):
            s = unicode(s, 'ISO-8859-1')
    return s

def smartUTF8(s):
    return smartUnicode(s).encode('utf-8')

def path_leaf(path):
    path, filename = ntpath.split(path)
    return {"path":path, "filename":filename}

def writeFile( data, filename ):
    try:
        thefile = open( filename, 'wb' )
        thefile.write( data )
        thefile.close()
    except IOError, e:
        log( 'unable to write data to ' + filename )
        log( e )
        return False
    except Exception, e:
        log( 'unknown error while writing data to ' + filename, url )
        log( e )
        return False
    return True

def readFile( filename ):
    if xbmcvfs.exists( filename):
        try:
            the_file = open (filename, 'r')
            data = the_file.read()
            the_file.close()
        except IOError:
            log( 'unable to read data from ' + filename )
            return ''
        except Exception, e:
            log( 'unknown error while reading data from ' + filename )
            log( e )
            return ''
        return data
    else:
        return ''


class Main:
    def __init__( self ):
        if sys.version_info >= (2, 7):
            log( 'the python verison is greater than or equal to 2.7' )
        else:
            log( 'the python verison is less than 2.7' )
        self._init_vars()
        self._get_settings()
        self._make_dirs()
        if self.HASHLIST == 'true':
            self._generate_hashlist()
        if self.MIGRATE == 'true':
            self._migrate()


    def _init_vars( self ):
        self.HASHLIST = ''
        self.HASHLISTFOLDER = ''
        self.HASHLISTFILE = ''
        self.MIGRATE = ''
        self.MIGRATETYPE = ''
        self.MIGRATEFOLDER = ''


    def _get_settings( self ):
        self.HASHLIST = __addon__.getSetting( "hashlist" )
        if self.HASHLIST == 'true':
            if __addon__.getSetting( "hashlist_path" ):
                self.HASHLISTFOLDER = __addon__.getSetting( "hashlist_path" ).decode('utf-8')
            else:
                self.HASHLISTFOLDER = xbmc.translatePath('special://profile/addon_data/%s/' % __addonname__ ).decode('utf-8')
            log( 'set hash list path to %s' % self.HASHLISTFOLDER )
            self.HASHLISTFILE = os.path.join( self.HASHLISTFOLDER, 'as_hashlist.txt' )
        self.MIGRATE = __addon__.getSetting( "migrate" )
        if self.MIGRATE == 'true':
            self.MIGRATETYPE = __addon__.getSetting( "migrate_type" )
            log( 'migrate type is %s' % self.MIGRATETYPE )
            if __addon__.getSetting( "migrate_path" ):
                self.MIGRATEFOLDER = __addon__.getSetting( "migrate_path" ).decode('utf-8')
                log( 'set migrate folder to %s' % self.MIGRATEFOLDER )
            else:
                self.MIGRATEFOLDER = ''
                log( 'no migration folder set' )
            

    def _make_dirs( self ):
        checkDir( xbmc.translatePath('special://profile/addon_data/%s' % __addonname__ ).decode('utf-8') )
        if self.HASHLISTFOLDER:
            checkDir( self.HASHLISTFOLDER )
        if self.MIGRATEFOLDER:
            checkDir( self.MIGRATEFOLDER )


    def _generate_hashlist( self ):
        hashmap = self._get_artists_hashmap()
        hashmap_str = ''
        keys = hashmap.keys()
        for item in keys:
           hashmap_str = hashmap_str + hashmap[item] + '\t' + item + '\n'
        if writeFile( hashmap_str, self.HASHLISTFILE ):
            log ('successfully wrote hash list file out to disk')
        else:
            log ('unable to write has list file out to disk')
                        

    def _migrate( self ):
        #nothing here yet
        return ''


    def _get_artists_hashmap( self ):
        #gets a list of all the artists from XBMC
        hashmap = OrderedDict()
        response = xbmc.executeJSONRPC ( '{"jsonrpc":"2.0", "method":"AudioLibrary.GetArtists", "params":{"albumartistsonly":false, "sort":{"order":"ascending", "ignorearticle":true, "method":"artist"}},"id": 1}}' )
        try:
            artists_info = json.loads(response)['result']['artists']
        except (IndexError, KeyError, ValueError):
            artists_info = []
        except Exception, e:
            log( 'unexpected error getting JSON back from XBMC' )
            log( e )
            artists_info = []
        if artists_info:
            for artist_info in artists_info:
            	artist_hash = self._hash_artist( artist_info['artist'] )
                hashmap[artist_hash] = artist_info['artist']
            hashmap[self._hash_artist( "Various Artists" )] = "Various Artists" 
        return hashmap


    def _move_files( self, old_loc, new_loc, type ):
        log( 'attempting to move from %s to %s' % (old_loc, new_loc) )
        try:
            os.chdir( old_loc )
            folders = os.listdir( old_loc )
        except OSError:
            log( 'no directory found: ' + old_loc )
            return
        except Exception, e:
            log( 'unexpected error while getting directory list' )
            log( e )
            return
        for folder in folders:
            if type == 'cache':
                old_folder = os.path.join( old_loc, folder )
                new_folder = os.path.join( new_loc, folder )
            elif type == 'local':
                old_folder = os.path.join( old_loc, folder, self.FANARTFOLDER )
                new_folder = os.path.join( new_loc, xbmc.getCacheThumbName(folder).replace('.tbn', '') )
            try:
                old_files = os.listdir( old_folder )
            except Exception, e:
                log( 'unexpected error while getting directory list' )
                log( e )
                old_files = []
            exclude_path = os.path.join( old_folder, '_exclusions.nfo' )
            if old_files and type == 'cache' and not xbmcvfs.exists(exclude_path):
                writeFile( '', exclude_path )
            for old_file in old_files:
                if old_file.endswith( '.nfo' ) and not old_file == '_exclusions.nfo':
                    checkDir( new_folder )
                    new_file = old_file.strip('_')
                    if new_file == 'artistimagesfanarttv.nfo':
                        new_file = 'fanarttvartistimages.nfo'
                    elif new_file == 'artistimageshtbackdrops.nfo':
                        new_file = 'htbackdropsartistimages.nfo'
                    elif new_file == 'artistimageslastfm.nfo':
                        new_file = 'lastfmartistimages.nfo'
                    elif new_file == 'artistbio.nfo':
                        new_file = 'lastfmartistbio.nfo'
                    elif new_file == 'artistsalbums.nfo':
                        new_file = 'lastfmartistalbums.nfo'
                    elif new_file == 'artistsimilar.nfo':
                        new_file = 'lastfmartistsimilar.nfo'
                    xbmcvfs.rename( os.path.join(old_folder, old_file), os.path.join(new_folder, new_file) )
                    log( 'moving %s to %s' % (old_file, os.path.join(new_folder, new_file)) )


    def _hash_artist(self, theartist):
        return xbmc.getCacheThumbName(theartist).replace('.tbn', '')


if ( __name__ == "__main__" ):
    log('script version %s started' % __addonversion__)
    slideshow = Main()

log('script stopped')