#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2013 Tristan Fischer (sphere@dersphere.de)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from xbmcswift2 import Plugin, xbmc, xbmcgui, NotFoundException
from resources.lib.api import JamendoApi


STRINGS = {
    # Root menu entries

    # Context menu
    'addon_settings': 30100,

    # Dialogs

    # Error dialogs
    'connection_error': 30120,
    'wrong_credentials': 30121,
    'want_set_now': 30122,
    # Noticications

    # Help Dialog

}


class Plugin_patched(Plugin):

    def _dispatch(self, path):
        for rule in self._routes:
            try:
                view_func, items = rule.match(path)
            except NotFoundException:
                continue
            self._request.view = view_func.__name__  # added
            self._request.view_params = items  # added
            listitems = view_func(**items)
            if not self._end_of_directory and self.handle >= 0:
                if listitems is None:
                    self.finish(succeeded=False)
                else:
                    listitems = self.finish(listitems)
            return listitems
        raise NotFoundException('No matching view found for %s' % path)


plugin = Plugin_patched()
api = JamendoApi(client_id='b6747d04')


@plugin.route('/')
def show_root():
    items = [
        {'label': _('show_albums'),
         'path': plugin.url_for(endpoint='show_albums')},
        {'label': _('show_artists'),
         'path': plugin.url_for(endpoint='show_artists')},
        {'label': _('show_radios'),
         'path': plugin.url_for(endpoint='show_radios')},
    ]
    return plugin.finish(items)


@plugin.route('/albums/<artist_id>/', name='show_albums_by_artist')
@plugin.route('/albums/')
def show_albums(artist_id=None):
    def context_menu(artist_id):
        return [
            (
                _('album_info'),
                'XBMC.Action(Info)'
            ),
            (
                _('all_albums_by_this_artist'),
                _view(
                    endpoint='show_albums_by_artist',
                    artist_id=artist_id,
                    is_update='true'
                )
            ),
            (
                _('addon_settings'),
                _run(
                    endpoint='open_settings'
                )
            ),
        ]

    plugin.set_content('albums')

    page = int(plugin.request.args.get('page', ['1'])[0])
    albums = api.get_albums(page=page, artist_id=artist_id)
    has_next_page = len(albums) == api.current_limit
    has_previous_page = page > 1
    is_update = 'is_update' in plugin.request.args

    items = [{
        'label': '%s - %s' % (album['artist_name'], album['name']),
        'info': {
            'count': i,
            'artist': album['artist_name'],
            'album': album['name'],
            'year': int(album.get('releasedate', '0.0.0').split('-')[0]),
        },
        'context_menu': context_menu(
            artist_id=album['artist_id']
        ),
        'replace_context_menu': True,
        'thumbnail': album['image'],
        'path': plugin.url_for(
            endpoint='show_tracks',
            album_id=album['id']
        )
    } for i, album in enumerate(albums)]

    if has_next_page:
        items.append({
            'label': '>> %s >>' % _('next'),
            'path': plugin.url_for(
                endpoint=plugin.request.view,
                is_update='true',
                **dict(plugin.request.view_params, page=int(page) + 1)
            )
        })

    if has_previous_page:
        items.insert(0, {
            'label': '<< %s <<' % _('previous'),
            'path': plugin.url_for(
                endpoint=plugin.request.view,
                is_update='true',
                **dict(plugin.request.view_params, page=int(page) - 1)
            )
        })

    finish_kwargs = {
        'update_listing': is_update
    }
    if plugin.get_setting('force_viewmode', bool):
        finish_kwargs['view_mode'] = 'thumbnail'
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/artists/')
def show_artists():
    def context_menu():
        return [
            (
                _('addon_settings'),
                _run(
                    endpoint='open_settings'
                )
            ),
        ]

    plugin.set_content('artists')

    page = int(plugin.request.args.get('page', ['1'])[0])
    artists = api.get_artists(page=page)
    has_next_page = len(artists) == api.current_limit
    has_previous_page = page > 1
    is_update = 'is_update' in plugin.request.args

    items = [{
        'label': artist['name'],
        'info': {
            'count': i,
            'artist': artist['name'],
        },
        'context_menu': context_menu(),
        'replace_context_menu': True,
        'thumbnail': image_helper(artist['image']),
        'path': plugin.url_for(
            endpoint='show_albums_by_artist',
            artist_id=artist['id'],
        )
    } for i, artist in enumerate(artists)]

    if has_next_page:
        items.append({
            'label': '>> %s >>' % _('next'),
            'path': plugin.url_for(
                endpoint=plugin.request.view,
                is_update='true',
                **dict(plugin.request.view_params, page=int(page) + 1)
            )
        })

    if has_previous_page:
        items.insert(0, {
            'label': '<< %s <<' % _('previous'),
            'path': plugin.url_for(
                endpoint=plugin.request.view,
                is_update='true',
                **dict(plugin.request.view_params, page=int(page) - 1)
            )
        })

    finish_kwargs = {
        'update_listing': is_update
    }
    if plugin.get_setting('force_viewmode', bool):
        finish_kwargs['view_mode'] = 'thumbnail'
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/radios/')
def show_radios():
    def context_menu():
        return [
            (
                _('addon_settings'),
                _run(
                    endpoint='open_settings'
                )
            ),
        ]

    plugin.set_content('music')

    page = int(plugin.request.args.get('page', ['1'])[0])
    radios = api.get_radios(page=page)
    has_next_page = len(radios) == api.current_limit
    has_previous_page = page > 1
    is_update = 'is_update' in plugin.request.args

    items = [{
        'label': radio['dispname'],
        'info': {
            'count': i,
        },
        'context_menu': context_menu(),
        'replace_context_menu': True,
        'thumbnail': radio['image'],
        'path': plugin.url_for(
            endpoint='play_song',  # FIXME
            track_id=radio['id'],
        )
    } for i, radio in enumerate(radios)]

    if has_next_page:
        items.append({
            'label': '>> %s >>' % _('next'),
            'path': plugin.url_for(
                endpoint=plugin.request.view,
                is_update='true',
                **dict(plugin.request.view_params, page=int(page) + 1)
            )
        })

    if has_previous_page:
        items.insert(0, {
            'label': '<< %s <<' % _('previous'),
            'path': plugin.url_for(
                endpoint=plugin.request.view,
                is_update='true',
                **dict(plugin.request.view_params, page=int(page) - 1)
            )
        })

    finish_kwargs = {
        'update_listing': is_update
    }
    if plugin.get_setting('force_viewmode', bool):
        finish_kwargs['view_mode'] = 'thumbnail'
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/tracks/album/<album_id>/')
def show_tracks(album_id):
    def context_menu(artist_id, track_id):
        return [
            (
                _('song_info'),
                'XBMC.Action(Info)'
            ),
            (
                _('all_albums_by_this_artist'),
                _view(
                    endpoint='show_albums_by_artist',
                    artist_id=artist_id,
                )
            ),
            (
                _('addon_settings'),
                _run(
                    endpoint='open_settings'
                )
            ),
        ]

    plugin.set_content('songs')

    album, tracks = api.get_album_tracks(album_id=album_id)

    items = [{
        'label': '%s - %s' % (album['artist_name'], track['name']),
        'info': {
            'count': i,
            'tracknumber': i + 1,
            'duration': track['duration'],
            'artist': album['artist_name'],
            'album': album['name'],
            'year': int(album.get('releasedate', '0.0.0').split('-')[0]),
        },
        'context_menu': context_menu(
            artist_id=album['artist_id'],
            track_id=track['id']
        ),
        'replace_context_menu': True,
        'is_playable': True,
        'thumbnail': album['image'],
        'path': plugin.url_for(
            endpoint='play_song',
            track_id=track['id']
        )
    } for i, track in enumerate(tracks)]
    return items


@plugin.route('/play/track/<track_id>')
def play_song(track_id):
    stream_url = api.get_track_url(track_id)
    return plugin.set_resolved_url(stream_url)


@plugin.route('/settings')
def open_settings():
    plugin.open_settings()


def _run(*args, **kwargs):
    return 'XBMC.RunPlugin(%s)' % plugin.url_for(*args, **kwargs)


def _view(*args, **kwargs):
    return 'XBMC.Container.Update(%s)' % plugin.url_for(*args, **kwargs)


def image_helper(url):
    if url:
        # fix whitespace in some image urls
        return url.replace(' ', '%20')
    else:
        addon_id = plugin._addon.getAddonInfo('id')
        icon = 'special://home/addons/%s/icon.png' % addon_id
        return icon


def log(text):
    plugin.log.info(text)


def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        #log('String is missing: %s' % string_id)
        return string_id

if __name__ == '__main__':
    plugin.run()