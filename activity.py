#! /usr/bin/env python
# -*- coding: utf-8 -*-

from gettext import gettext as _

import gtk

from sugar.activity import activity
from sugar.graphics.toolbarbox import ToolbarBox
from sugar.activity.widgets import ActivityToolbarButton
from sugar.activity.widgets import StopButton
from sugar.graphics.colorbutton import ColorToolButton
from sugar.graphics.toolbarbox import ToolbarButton
from sugar.graphics.toolbutton import ToolButton

import sugargame.canvas

import reversi


class ReversiActivity(activity.Activity):
    def __init__(self, handle):
        activity.Activity.__init__(self, handle)
        self.sound_enable = True
        self.game = reversi.ReversiController(self)
        self.build_toolbar()
        self._pygamecanvas = sugargame.canvas.PygameCanvas(self)
        self.set_canvas(self._pygamecanvas)
        self._pygamecanvas.grab_focus()
        self._pygamecanvas.run_pygame(self.game.run)

    def build_toolbar(self):
        toolbar_box = ToolbarBox()
        self.set_toolbar_box(toolbar_box)
        toolbar_box.show()

        activity_button = ActivityToolbarButton(self)
        toolbar_box.toolbar.insert(activity_button, -1)
        activity_button.show()

        separator = gtk.SeparatorToolItem()
        toolbar_box.toolbar.insert(separator, -1)
        separator.show()

        self.build_colors_toolbar(toolbar_box)

        separator = gtk.SeparatorToolItem()
        toolbar_box.toolbar.insert(separator, -1)
        separator.show()

        # new game button
        new_game = ToolButton('new-game')
        new_game.connect('clicked', self._new_game)
        new_game.set_tooltip(_('New game'))
        toolbar_box.toolbar.insert(new_game, -1)

        separator = gtk.SeparatorToolItem()
        toolbar_box.toolbar.insert(separator, -1)
        separator.show()

        #current
        item = gtk.ToolItem()
        label = gtk.Label()
        label.set_text(' %s ' % _('Current player:'))
        item.add(label)
        toolbar_box.toolbar.insert(item, -1)

        #player
        item = gtk.ToolItem()
        self.current_label = gtk.Label()
        self.current_label.set_text(' %s' % 1)
        item.add(self.current_label)
        toolbar_box.toolbar.insert(item, -1)

        separator = gtk.SeparatorToolItem()
        toolbar_box.toolbar.insert(separator, -1)
        separator.show()

        sound_button = ToolButton('speaker-muted-100')
        sound_button.set_tooltip(_('Sound'))
        sound_button.connect('clicked', self.sound_control)
        toolbar_box.toolbar.insert(sound_button, -1)

        # separator and stop
        separator = gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbar_box.toolbar.insert(separator, -1)
        separator.show()

        stop_button = StopButton(self)
        toolbar_box.toolbar.insert(stop_button, -1)
        stop_button.show()

        self.show_all()

    def build_colors_toolbar(self, toolbox):

        colors_bar = gtk.Toolbar()

        ########################################################################
        # Point color
        item = gtk.ToolItem()
        label = gtk.Label()
        label.set_text('%s ' % _('Player 1'))
        item.add(label)
        colors_bar.insert(item, -1)

        # select color
        item = gtk.ToolItem()
        _fill_color = ColorToolButton()
        c = gtk.gdk.Color()
        c.red = 65535
        c.green = 65535
        c.blue = 65535
        _fill_color.set_color(c)
        _fill_color.connect('notify::color', self.color_player1_change)
        item.add(_fill_color)
        colors_bar.insert(item, -1)

        # Separator
        separator = gtk.SeparatorToolItem()
        colors_bar.insert(separator, -1)
        separator.show()

        ########################################################################
        # Back color
        item = gtk.ToolItem()
        label = gtk.Label()
        label.set_text('%s ' % _('Player 2'))
        item.add(label)
        colors_bar.insert(item, -1)

        # select color
        item = gtk.ToolItem()
        _fill_color = ColorToolButton()
        c = gtk.gdk.Color()
        c.red = 0
        c.green = 0
        c.blue = 0
        _fill_color.set_color(c)
        _fill_color.connect('notify::color', self.color_player2_change)
        item.add(_fill_color)
        colors_bar.insert(item, -1)

        # Separator
        separator = gtk.SeparatorToolItem()
        colors_bar.insert(separator, -1)
        separator.show()

        ########################################################################
        # Line color
        item = gtk.ToolItem()
        label = gtk.Label()
        label.set_text('%s ' % _('Lines'))
        item.add(label)
        colors_bar.insert(item, -1)

        # select color
        item = gtk.ToolItem()
        _fill_color = ColorToolButton()
        _fill_color.connect('notify::color', self.color_line_change)
        item.add(_fill_color)
        colors_bar.insert(item, -1)

        # Separator
        separator = gtk.SeparatorToolItem()
        colors_bar.insert(separator, -1)
        separator.show()

        ########################################################################
        # Line color
        item = gtk.ToolItem()
        label = gtk.Label()
        label.set_text('%s ' % _('Background'))
        item.add(label)
        colors_bar.insert(item, -1)

        # select color
        item = gtk.ToolItem()
        _fill_color = ColorToolButton()
        _fill_color.connect('notify::color', self.color_back_change)
        item.add(_fill_color)
        colors_bar.insert(item, -1)

        # Separator
        separator = gtk.SeparatorToolItem()
        colors_bar.insert(separator, -1)
        separator.show()

        ########################################################################
        # Line color
        item = gtk.ToolItem()
        label = gtk.Label()
        label.set_text('%s ' % _('Board'))
        item.add(label)
        colors_bar.insert(item, -1)

        # select color
        item = gtk.ToolItem()
        _fill_color = ColorToolButton()
        _fill_color.connect('notify::color', self.color_board_change)
        item.add(_fill_color)
        colors_bar.insert(item, -1)

        ########################################################################
        colors_bar.show_all()
        colors_button = ToolbarButton(label=_('Colors'),
                page=colors_bar,
                icon_name='toolbar-colors')
        toolbox.toolbar.insert(colors_button, -1)
        colors_button.show()

    def _new_game(self, widget):
        self.game.handle_restart_button_click()

    def color_player1_change(self, widget, pspec):
        color = widget.get_color()
        new_color = self.color_to_rgb(color)
        self.game.set_player1_color(new_color)

    def color_player2_change(self, widget, pspec):
        color = widget.get_color()
        new_color = self.color_to_rgb(color)
        self.game.set_player2_color(new_color)

    def color_line_change(self, widget, pspec):
        color = widget.get_color()
        new_color = self.color_to_rgb(color)
        self.game.set_line_color(new_color)

    def color_back_change(self, widget, pspec):
        color = widget.get_color()
        new_color = self.color_to_rgb(color)
        self.game.set_back_color(new_color)

    def color_board_change(self, widget, pspec):
        color = widget.get_color()
        new_color = self.color_to_rgb(color)
        self.game.set_board_color(new_color)

    def color_to_rgb(self, color):
        r = color.red *255 / 65535
        g = color.green *255 / 65535
        b = color.blue *255 / 65535
        return (r, g, b)

    def set_current_player(self, player):
        self.current_label.set_text(' %s' % player)

    def sound_control(self, button):
        self.sound_enable = not self.sound_enable
        self.game.change_sound(self.sound_enable)
        if not self.sound_enable:
            button.set_icon('speaker-muted-000')
            button.set_tooltip(_('No sound'))
        else:
            button.set_icon('speaker-muted-100')
            button.set_tooltip(_('Sound'))

