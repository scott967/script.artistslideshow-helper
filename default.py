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
    import simplejson as json
    from resources.ordereddict.ordereddict import OrderedDict

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
        xbmcvfs.mkdirs(path)

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
    if type(data).__name__=='unicode':
        data = data.encode('utf-8')
    try:
        thefile = open( filename, 'wb' )
        thefile.write( data )
        thefile.close()
    except IOError, e:
        log( 'unable to write data to ' + filename )
        log( e )
        return False
    except Exception, e:
        log( 'unknown error while writing data to ' + filename )
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
        command = 'XBMC.Notification(%s, %s, %s, %s)' % (smartUTF8(__language__(30300)), smartUTF8(__language__(30301)), 5000, smartUTF8(__addonicon__))
        xbmc.executebuiltin(command)
        self._init_vars()
        self._get_settings()
        self._make_dirs()
        if self.HASHLIST == 'false' and self.MIGRATE == 'false':
            command = 'XBMC.Notification(%s, %s, %s, %s)' % (smartUTF8(__language__(30350)), smartUTF8(__language__(30351)), 5000, smartUTF8(__addonicon__))
            xbmc.executebuiltin(command)
            return        
        if self.HASHLIST == 'true' and self.HASHLISTFOLDER:
            self._generate_hashlist()
        elif self.HASHLIST == 'true' and not self.HASHLISTFOLDER:
            command = 'XBMC.Notification(%s, %s, %s, %s)' % (smartUTF8(__language__(30340)), smartUTF8(__language__(30341)), 5000, smartUTF8(__addonicon__))
            xbmc.executebuiltin(command)
        if self.MIGRATE == 'true' and self.MIGRATEFOLDER:
            self._migrate()
        elif self.MIGRATE == 'true' and not self.MIGRATEFOLDER:
            command = 'XBMC.Notification(%s, %s, %s, %s)' % (smartUTF8(__language__(30320)), smartUTF8(__language__(30321)), 5000, smartUTF8(__addonicon__))
            xbmc.executebuiltin(command)
            


    def _init_vars( self ):
        self.HASHLIST = ''
        self.HASHLISTFOLDER = ''
        self.HASHLISTFILE = ''
        self.MIGRATE = ''
        self.MIGRATETYPE = ''
        self.MIGRATEFOLDER = ''
        self.ASCACHEFOLDER = xbmc.translatePath( 'special://profile/addon_data/script.artistslideshow/ArtistSlideshow' ).decode('utf-8')


    def _get_settings( self ):
        self.HASHLIST = __addon__.getSetting( "hashlist" )
        if self.HASHLIST == 'true':
            self.HASHLISTFOLDER = __addon__.getSetting( "hashlist_path" ).decode('utf-8')
            log( 'set hash list path to %s' % self.HASHLISTFOLDER )
            self.HASHLISTFILE = os.path.join( self.HASHLISTFOLDER, 'as_hashlist.txt' )
        self.MIGRATE = __addon__.getSetting( "migrate" )
        if self.MIGRATE == 'true':
            mtype = __addon__.getSetting( "migrate_type" )
            if mtype == '2':
                self.MIGRATETYPE = 'copy'
            elif mtype == '1':
                self.MIGRATETYPE = 'move'
            elif mtype == '0':
                self.MIGRATETYPE = 'test'
            log( 'raw migrate type is %s, so migrate type is %s' % (mtype, self.MIGRATETYPE) )
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
        for key, value in hashmap.iteritems():
           hashmap_str = hashmap_str + value + '\t' + key + '\n'
        if writeFile( hashmap_str, self.HASHLISTFILE ):
            message = __language__(30311)
            log ('successfully wrote hash list file out to disk')
        else:
            message = __language__(30312)
            log ('unable to write has list file out to disk')
        command = 'XBMC.Notification(%s, %s, %s, %s)' % (smartUTF8(__language__(30310)), smartUTF8(message), 5000, smartUTF8(__addonicon__))
        xbmc.executebuiltin(command)
                        


    def _migrate( self ):
        log( 'attempting to %s images from Artist Slideshow cache directory' % self.MIGRATETYPE )
        test_str = ''
        checkDir(self.MIGRATEFOLDER)
        hashmap = self._get_artists_hashmap()
        try:
            os.chdir( self.ASCACHEFOLDER )
            folders = os.listdir( self.ASCACHEFOLDER )
        except OSError:
            log( 'no directory found: ' + self.ASCACHEFOLDER )
            return
        except Exception, e:
            log( 'unexpected error while getting directory list' )
            log( e )
            return
        for folder in folders:
            try:
                artist_name = hashmap[folder].decode('utf-8')
            except KeyError:
                log( 'no matching artist folder for: ' + folder )
                artist_name = ''
            except Exception, e:
                log( 'unexpected error while finding matching artist for ' + folder )
                log( e )
                artist_name = ''
            if artist_name:
                old_folder = os.path.join( self.ASCACHEFOLDER, folder )
                new_folder = os.path.join( self.MIGRATEFOLDER, artist_name, 'extrafanart' )
                if self.MIGRATETYPE == 'copy' or self.MIGRATETYPE == 'move':
                    checkDir(new_folder)
                try:
                    os.chdir( old_folder )
                    files = os.listdir( old_folder )
                except OSError:
                    log( 'no directory found: ' + old_folder )
                    return
                except Exception, e:
                    log( 'unexpected error while getting file list' )
                    log( e )
                    return
                log( '%s %s to %s' % (self.MIGRATETYPE, folder, new_folder) )
                for file in files:
                    old_file = os.path.join(old_folder, file)
                    new_file = os.path.join(new_folder, file)
                    if self.MIGRATETYPE == 'move':
                        xbmcvfs.rename( old_file, new_file  )
                    elif self.MIGRATETYPE == 'copy':                
                        xbmcvfs.copy( old_file, new_file )
                    else:
                        test_str = test_str + old_file + ' to ' + new_file + '\n'
                if self.MIGRATETYPE == 'move':
                    xbmcvfs.rmdir ( old_folder )
        if self.MIGRATETYPE == 'test':
            writeFile( test_str, os.path.join( self.MIGRATEFOLDER, '_migrationtest.txt' ) )
        command = 'XBMC.Notification(%s, %s, %s, %s)' % (smartUTF8(__language__(30330)), smartUTF8(__language__(30331)), 5000, smartUTF8(__addonicon__))
        xbmc.executebuiltin(command)


    def _hash_artist(self, theartist):
        return xbmc.getCacheThumbName(theartist).replace('.tbn', '')


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


if ( __name__ == "__main__" ):
    log('script version %s started' % __addonversion__)
    slideshow = Main()

log('script stopped')