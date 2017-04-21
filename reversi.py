#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Reversi.py - An implementation of Reversi for OLPC laptops.
# Copyright (C) 2007 David Lee Ludwig <dludwig at pobox dot com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import math
import os
import pygame
import random
import gtk

from gettext import gettext as _


# Immutable Globals / Settings
screen_size = (1200, 825)
background_color = (255, 255, 255)
background_board_color = (255, 255, 255)
cell_padding_color = (0, 0, 0)
available_cell_color = (0, 0, 0)
player_view_outline_color = (0, 0, 0)
player_view_outline_width = 1
player_indicator_color = (0, 0, 0)
player_indicator_size = (8, 32)
num_columns = 8
num_rows = 8
cell_padding = 4

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

player_numbers_to_piece_names = [None, "White", "Black"]


def load_sound(relative_path_name):
    full_path_name = os.path.abspath(os.path.join('data', relative_path_name))
    sound = pygame.mixer.Sound(full_path_name)
    return sound



#===============================================================================
# Views
#===============================================================================

class CellView(pygame.sprite.Sprite):
    def __init__(self, rect, board_coord):
        pygame.sprite.Sprite.__init__(self)

        # Init rect (in screen coords)
        self.rect = rect
        
        # Init position (in board coords)
        self.board_coord = board_coord
        
        # Create an image and clear it
        self.image = pygame.Surface(self.rect.size)
        self.show_no_piece()

    def show_piece(self, color):
        """Shows a piece in the cell.  Set color to "Black" or "White"."""
        global background_board_color

        self.image.fill(background_board_color)

        piece_width = self.rect.width * 0.8
        border_size = self.rect.width * 0.05
        pos = (self.rect.centerx - self.rect.left, self.rect.centery - self.rect.top)
        #Colors of black and white circles
        if color == "Black":
            pygame.draw.circle(self.image, BLACK, pos, int(piece_width / 2))
        elif color == "White":
            if WHITE == (255, 255, 255):
                pygame.draw.circle(self.image, (0, 0, 0), pos, int(piece_width / 2), int(border_size))
            else:
                pygame.draw.circle(self.image, WHITE, pos, int(piece_width / 2))
    
    def show_no_piece(self):
        """Clears the cell, showing no piece at all."""
        global background_board_color

        self.image = pygame.Surface(self.rect.size)
        self.image.fill(background_board_color)
    
    def show_as_available(self, piece_color_name = "Black"):
        #self.draw_corners()
        self.draw_dot(piece_color_name)
        
    def draw_corners(self):
        padding = int(self.rect.width * 0.05)
        size = int(self.rect.width * 0.1)

        left = padding
        right = self.rect.width - padding - 1
        top = padding
        bottom = self.rect.height - padding - 1
        
        pointlist = [(left, top),
                     (left, top + size),
                     (left + size, top)]
        pygame.draw.polygon(self.image, available_cell_color, pointlist)
        
        pointlist = [(right, top),
                     (right - size, top),
                     (right, top + size)]
        pygame.draw.polygon(self.image, available_cell_color, pointlist)
        
        pointlist = [(right, bottom),
                     (right, bottom - size),
                     (right - size, bottom)]
        pygame.draw.polygon(self.image, available_cell_color, pointlist)

        pointlist = [(left, bottom),
                     (left + size, bottom),
                     (left, bottom - size)]
        pygame.draw.polygon(self.image, available_cell_color, pointlist)
        
    def draw_dot(self, color):
        pos = (self.rect.centerx - self.rect.left, self.rect.centery - self.rect.top)
        if color == "Black":
            radius = int(self.rect.width * 0.05)
            pygame.draw.circle(self.image, (0, 0, 0), pos, radius)
        elif color == "White":
            radius = int(self.rect.width * 0.07)
            width = 2
            pygame.draw.circle(self.image, (0, 0, 0), pos, radius, width)
    
    def update_from_cell_model(self, cell_model, is_available, active_piece_color_name):
        if cell_model.has_piece():
            self.show_piece(cell_model.get_piece_name())
        else:
            self.show_no_piece()
        
        if is_available:
            self.show_as_available(active_piece_color_name)


class BoardView:
    def __init__(self, controller, top_left, size_in_pixels, grid_size):
        self.controller = controller
        
        self.top_left = top_left
        self.grid_size = grid_size
        self.num_columns = grid_size[0]
        self.num_rows = grid_size[1]
        self.size_in_pixels = size_in_pixels

        # Init cells
        cell_width = (size_in_pixels[0] - (cell_padding * (grid_size[0] + 1))) / grid_size[0]
        cell_height = (size_in_pixels[1] - (cell_padding * (grid_size[1] + 1))) / grid_size[1]
        self.cell_size = (cell_width, cell_height)

        self.background = pygame.Surface(self.size_in_pixels)
        self.init_cell_views(self.cell_size, self.grid_size)

        self.redraw_background()
        
    def redraw_background(self):
        # Draw board background
        self.draw_board_background(self.cell_size, self.grid_size)

    def init_cell_views(self, cell_size, grid_size):
        # Create a group to store the cells in.
        self.cell_view_group = pygame.sprite.OrderedUpdates()
        
        # Create a 2D array to store the cells in, which will be accessible via column then row.
        self.cell_view_grid = []

        # Create each cell
        cell_rect = pygame.Rect(0, 0, cell_size[0], cell_size[1])
        for column_index in range(grid_size[0]):
            grid_column = []

            cell_rect.top = self.top_left[1] + cell_padding + (column_index * (cell_padding + cell_size[1]))

            for row_index in range(grid_size[1]):
                cell_rect.left = self.top_left[0] + cell_padding + (row_index * (cell_padding + cell_size[0]))
                
                copy_of_cell_rect = pygame.Rect(cell_rect)
                cell_view = CellView(copy_of_cell_rect, (column_index, row_index))
                self.cell_view_group.add(cell_view)
                grid_column.append(cell_view)
            
            self.cell_view_grid.append(grid_column)
    
    def draw_board_background(self, cell_size, grid_size):
        # tablero
        background_color = (100, 100, 100)
        self.background.fill(background_color)
        
        drawn_height = cell_padding + (grid_size[1] * (cell_padding + cell_size[1]))
        tmp_rect = pygame.Rect(0, 0, cell_padding, drawn_height)
        for column_index in range(grid_size[0] + 1):
            tmp_rect.left = column_index * (cell_padding + cell_size[0])
            self.background.fill(cell_padding_color, tmp_rect)
    
        drawn_width = cell_padding + (grid_size[0] * (cell_padding + cell_size[0]))
        tmp_rect = pygame.Rect(0, 0, drawn_width, cell_padding)
        for row_index in range(grid_size[0] + 1):
            tmp_rect.top = row_index * (cell_padding + cell_size[1])
            self.background.fill(cell_padding_color, tmp_rect)
    
    def get_num_columns(self):
        return self.num_columns
    
    def get_num_rows(self):
        return self.num_rows
            
    def get_cell_view_at_screen_coord(self, screen_coord):
        for cell_view in self.cell_view_group:
            if cell_view.rect.collidepoint(screen_coord[0], screen_coord[1]):
                return cell_view
        return None
    
    def get_cell_view_at_board_coord(self, board_coord):
        return self.cell_view_grid[board_coord[0]][board_coord[1]]
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            cell_view = self.get_cell_view_at_screen_coord(event.pos)
            if cell_view:
                self.controller.handle_cell_click(cell_view.board_coord)
                return True

        return False
    
    def update_from_model(self, model):
        #board_model = model.get_board_model()
        for row_index in range(0, self.get_num_rows()):
            for column_index in range(0, self.get_num_columns()):
                cell_model = model.get_cell_model(column_index, row_index)

                is_available = model.is_cell_available_for_move(cell_model.get_board_coord())
                active_player_number = model.get_active_player_number()
                active_piece_color_name = player_numbers_to_piece_names[active_player_number]

                cell_view = self.get_cell_view_at_board_coord((column_index, row_index))
                cell_view.update_from_cell_model(cell_model, is_available, active_piece_color_name)
                #cell_view.update_from_model(model)
                
                # HACK
                #if column_index == 1 and row_index == 1:
                #    cell_view.show_as_available()
    
    def draw(self, surface):
        surface.blit(self.background, self.top_left)
        self.cell_view_group.draw(surface)


class PlayerView:
    def __init__(self, rect, player_number):
        self.rect = rect
        self.player_number = player_number
        self.update_image(1, False, 0)
        
    def update_from_model(self, model):
        player_model = model.get_player_model_from_number(self.player_number)
        piece_count = model.get_piece_count(player_model.get_piece_color_name())
        #board_model.get_piece_count(player_model.get_piece_color_name())
        self.update_image(player_model.get_player_number(), model.is_player_active(self.player_number), piece_count)
        
    def update_image(self, player_number, player_is_active, piece_count):
        self.image = pygame.Surface(self.rect.size)
        self.image.fill(background_color)  
        #self.draw_outline()
        self.draw_player_number(player_number)
        self.draw_piece_count(piece_count, player_numbers_to_piece_names[player_number])
        self.draw_player_active(player_is_active)
        
    def draw_outline(self):
        tmp_rect = pygame.Rect((0, 0), self.rect.size)
        pygame.draw.rect(self.image, player_view_outline_color, tmp_rect, 1)
        
    def draw_player_active(self, is_active):
        if is_active:
            tmp_rect = pygame.Rect((0, 0), self.rect.size)
            tmp_rect.height = 48
            tmp_rect.width -= 1
            pygame.draw.rect(self.image, (0, 0, 0), tmp_rect, 2)
#===============================================================================
#            # Draw a line below the player number
#            tmp_rect = pygame.Rect((0, 0), self.rect.size)
#            tmp_rect.height = 2
#            tmp_rect.top = 50
#            tmp_rect.inflate_ip(int(tmp_rect.width * -0.2), 0)
#            self.image.fill((0, 0, 0), tmp_rect)
#===============================================================================
        
    def draw_player_number(self, player_number):
        #global player_indicator_color
        tmp_rect = pygame.Rect((0, 0), player_indicator_size)
        piece_color_name = player_numbers_to_piece_names[player_number]
        if piece_color_name == "White":
            # draw one box, centered at the top of the view
            tmp_rect.centerx = self.rect.width / 2
            tmp_rect.top = 8
            self.image.fill(player_indicator_color, tmp_rect)
            #self.image.fill((255, 255, 255), tmp_rect.inflate(-4, -4))
        elif piece_color_name == "Black":
            # draw two boxes, centered at the top of the view
            tmp_rect.right = (self.rect.width / 2) - 4
            tmp_rect.top = 8
            self.image.fill(player_indicator_color, tmp_rect)
            tmp_rect.left = (self.rect.width / 2) + 4
            self.image.fill(player_indicator_color, tmp_rect)
            
    def draw_piece_count(self, piece_count, piece_name):
        mini_piece_image = self.create_mini_piece_image(piece_name)
        
        leftmost = 4
        topmost = 60
        max_columns = 5
        padding = 3
        horizontal_step = mini_piece_image.get_width() + padding
        vertical_step = mini_piece_image.get_height() + padding
        for top in range(topmost, self.rect.height - vertical_step, vertical_step):
            for left in range(leftmost, leftmost + (horizontal_step * max_columns), horizontal_step):
                if piece_count == 0:
                    return
                else:
                    self.image.blit(mini_piece_image, (left, top))
                    piece_count -= 1
        
    def create_mini_piece_image(self, piece_name):
        width = (self.rect.width - 20) / 5

        image = pygame.Surface((width, width))
        image.fill(background_color)

        if piece_name == "Black":
            pygame.draw.circle(image, BLACK, (width/2, width/2), width/2)
        elif piece_name == "White":
            if WHITE == (255, 255, 255):
                pygame.draw.circle(image, (0, 0, 0), (width/2, width/2), width/2, 2)
            else:
                pygame.draw.circle(image, WHITE, (width/2, width/2), width/2)
            
        return image
        
    def draw(self, surface):
        surface.blit(self.image, self.rect)


class RestartButton:
    def __init__(self, controller, rect, is_visible):
        self.controller = controller
        self.rect = rect
        self.is_visible = is_visible
        self.update_image()
        
    def set_visible(self, is_visible):
        self.is_visible = is_visible
    
    def update_image(self):
        self.image = pygame.Surface(self.rect.size)
        self.image.fill(background_color)
        self.image.set_colorkey(background_color)

        top_ellipse_rect = pygame.Rect((0, 0), self.rect.size)
        top_ellipse_rect.height = self.rect.height * 0.2
        pygame.draw.ellipse(self.image, (0, 0, 0), top_ellipse_rect, 3)
        
        bottom_ellipse_rect = pygame.Rect(top_ellipse_rect)
        bottom_ellipse_rect.width = self.rect.width * 0.8
        bottom_ellipse_rect.centerx = self.rect.width / 2
        bottom_ellipse_rect.bottom = self.rect.height
        pygame.draw.arc(self.image, (0, 0, 0), bottom_ellipse_rect, math.pi, 2 * math.pi, 3)

        pt1 = top_ellipse_rect.midleft
        pt2 = bottom_ellipse_rect.midleft
        pygame.draw.line(self.image, (0, 0, 0), pt1, pt2, 2)

        pt1 = (top_ellipse_rect.right - 2, top_ellipse_rect.centery)
        pt2 = (bottom_ellipse_rect.right - 2, bottom_ellipse_rect.centery)
        pygame.draw.line(self.image, (0, 0, 0), pt1, pt2, 2)
            
    def draw(self, surface):
        if self.is_visible:
            surface.blit(self.image, self.rect)
            
    def handle_event(self, event):
        if self.is_visible:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.rect.collidepoint(event.pos):
                    self.controller.handle_restart_button_click()
                    return True
        return False


class ReversiView:
    def __init__(self, controller, view_size, grid_size):
        # Setup board view
        use = (170 + 40 + 40) * 2
        width = view_size[0] - use
        height = view_size[1] - 75
        size = min(width, height)

        self.board_view = BoardView(controller, (250, 50), (size, size), grid_size)

        # Setup player views
        tmp_rect = pygame.Rect(40, 20, 170, 570)
        self.player_views = []
        self.player_views.append(None)
        self.player_views.append(PlayerView(pygame.Rect(tmp_rect), 1))
        tmp_rect.right = view_size[0] - 40
        self.player_views.append(PlayerView(pygame.Rect(tmp_rect), 2))
        
        # Setup end-of-game restart button
        self.restart_button = RestartButton(controller, pygame.Rect(60, 600, 130, 130), False)

    def update_from_model(self, model):
        self.board_view.update_from_model(model)

        for player_number in [1, 2]:
            player_view = self.player_views[player_number]
            player_view.update_from_model(model)

    def redraw_back(self):
        self.board_view.redraw_background()

    def draw(self, surface):
        surface.fill(background_color)

        self.board_view.draw(surface)

        for player_view in self.player_views:
            if player_view is not None:
                player_view.draw(surface)
                
        self.restart_button.draw(surface)
        
    def handle_event(self, event):
        if self.board_view.handle_event(event) == True:
            return True
        elif self.restart_button.handle_event(event) == True:
            return True
        else:
            return False
                


#===============================================================================
# Models
#===============================================================================

class CellModel:
    def __init__(self, board_coord):
        self.board_coord = board_coord
        self.piece_name = None
    
    def get_board_coord(self):
        return self.board_coord
        
    def has_piece(self, color_name = None):
        if color_name is None:
            return self.get_piece_name() is not None
        else:
            return self.get_piece_name() == color_name
    
    def get_piece_name(self):
        return self.piece_name
    
    def put_piece(self, piece_name):
        self.piece_name = piece_name
    
    def clear_piece(self):
        self.piece_name = None


class BoardModel:
    def __init__(self, grid_size):
        self.init_cell_models(grid_size)
        
    def init_cell_models(self, grid_size):
        self.cell_models = []
        for column_index in range(0, grid_size[0]):
            column = []
            for row_index in range(0, grid_size[1]):
                cell_model = CellModel((column_index, row_index))
                column.append(cell_model)

            self.cell_models.append(column)
    
    def get_cell_model(self, column_index, row_index):
        if column_index < 0 or row_index < 0 or column_index >= len(self.cell_models) or row_index >= len(self.cell_models[column_index]):
            return None
        else:
            return self.cell_models[column_index][row_index]
    
    def put_piece(self, piece_color_name, board_coord, toggle_cells,):
        cell_model = self.get_cell_model(board_coord[0], board_coord[1])
        cell_model.put_piece(piece_color_name)
        if toggle_cells:
            cells_to_toggle = self.get_toggleable_cells_at_coord(piece_color_name, board_coord)
            for cell_model in cells_to_toggle:
                cell_model.put_piece(piece_color_name)
            return len(cells_to_toggle)
        else:
            return 0
        
    def clear_piece(self, column_index, row_index):
        cell_model = self.get_cell_model(column_index, row_index)
        cell_model.clear_piece()
    
    def get_piece_count(self, piece_name):
        count = 0
        for column in self.cell_models:
            for cell_model in column:
                if cell_model.get_piece_name() == piece_name:
                    count += 1
        return count
    
    def is_cell_available_for_move(self, piece_color_name, board_coord):
        cell_model = self.get_cell_model(board_coord[0], board_coord[1])
        if cell_model.has_piece():
            return False
        else:
            cells_to_toggle = self.get_toggleable_cells_at_coord(piece_color_name, board_coord)
            return len(cells_to_toggle) > 0
    
    def get_toggleable_cells_at_coord(self, piece_color_name, board_coord):
        cells = []
        for step in [(0,-1), (1,-1), (1,0), (1,1), (0,1), (-1,1), (-1,0), (-1,-1)]: # directions to move in
            cells_to_add = self.get_toggleable_cells_in_direction(piece_color_name, board_coord, step)
            cells.extend(cells_to_add)
        return cells
    
    def get_toggleable_cells_in_direction(self, piece_color_name, starting_board_coord, step):
        cells = []
        cell_pos = [starting_board_coord[0], starting_board_coord[1]]
        while True:
            cell_pos[0] += step[0]
            cell_pos[1] += step[1]
            cell_model = self.get_cell_model(cell_pos[0], cell_pos[1])
            if cell_model and cell_model.has_piece():
                if cell_model.get_piece_name() is not piece_color_name:
                    cells.append(cell_model)
                else:
                    return cells
            else:
                return []

    def get_all_toggleable_cells(self, piece_color_name):
        cells = []
        for column in self.cell_models:
            for cell_model in column:
                if self.is_cell_available_for_move(piece_color_name, cell_model.get_board_coord()):
                    cells.append(cell_model)
        return cells                


class PlayerModel:
    def __init__(self, player_number):
        self.player_number = player_number
        self.piece_color_name = player_numbers_to_piece_names[player_number]
        
    def get_player_number(self):
        return self.player_number
    
    def get_piece_color_name(self):
        return self.piece_color_name


class ReversiModel:
    def __init__(self, parent, grid_size):
        self.parent = parent
        self.grid_size = grid_size

        self.current_player = 1

        self.board_model = BoardModel(grid_size)

        self.player_models = []
        self.player_models.append(None)
        self.player_models.append(PlayerModel(1))
        self.player_models.append(PlayerModel(2))
        
    def get_board_model(self):
        return self.board_model
    
    def get_cell_model(self, column_index, row_index):
        return self.board_model.get_cell_model(column_index, row_index)
    
    def get_player_model_from_number(self, player_number):
        return self.player_models[player_number]
    
    def get_player_model_from_color_name(self, piece_color_name):
        for player_model in self.player_models:
            if player_model is not None:
                if piece_color_name == player_model.get_piece_color_name():
                    return player_model
        return None
    
    def is_player_active(self, player_number):
        return player_number == self.current_player
    
    def set_current_player(self, player_number):
        self.current_player = player_number
        self.parent.set_current_player(self.current_player)

    def get_active_player_number(self):
        return self.current_player
        
    def get_inactive_player_number(self):
        if self.current_player == 1:
            return 2
        else:
            return 1
        
    def can_player_move(self, player_number):
        player_model = self.get_player_model_from_number(player_number)
        available_cells_to_match = self.board_model.get_all_toggleable_cells(player_model.get_piece_color_name())
        return len(available_cells_to_match) > 0
        
    def can_toggle_current_player(self):
        return self.can_player_move(self.get_inactive_player_number())

    def toggle_current_player(self):
        self.set_current_player(self.get_inactive_player_number())

    def setup_initial_pieces(self):
        for column in range(0, self.grid_size[0]):
            for row in range(0, self.grid_size[1]):
                self.board_model.clear_piece(column, row)
        
        self.board_model.put_piece("Black", (3,3), False)
        self.board_model.put_piece("White", (3,4), False)
        self.board_model.put_piece("White", (4,3), False)
        self.board_model.put_piece("Black", (4,4), False)
        
    def put_piece(self, board_coord):
        current_player_model = self.get_player_model_from_number(self.current_player)
        piece_color_name = current_player_model.get_piece_color_name()
        return self.board_model.put_piece(piece_color_name, board_coord, True)
    
    def get_piece_count(self, piece_color_name):
        #player_model = self.get_player_model_from_color_name(piece_color_name)
        return self.board_model.get_piece_count(piece_color_name)
    
    def is_cell_available_for_move(self, board_coord):
        player_model = self.get_player_model_from_number(self.current_player)
        return self.board_model.is_cell_available_for_move(player_model.get_piece_color_name(), board_coord)



#===============================================================================
# Controllers
#===============================================================================

class ReversiController:

    def __init__(self, parent=None):
        self.parent = parent
        self.sound_enable = True
        random.seed()
        self.clock = pygame.time.Clock()
     
    def get_state(self):
        return self.state_name
    
    def set_state(self, state_name):
        self.state_name = state_name
        if state_name == "StartGame":
            self.view.restart_button.set_visible(False)
            self.model.setup_initial_pieces()
            self.model.set_current_player(1)
            self.view.update_from_model(self.model)
            #self.board_view.get_cell_view_at_board_coord((0, 0)).show_as_available()
            self.set_state("WaitingForMove")
        elif state_name == "WaitingForMove":
            # Do nothing yet, wait for a move.
            pass
        elif state_name == "EndGame":
            self.play_sound("clapping")
            self.view.restart_button.set_visible(True)
            pass
        
    def handle_cell_click(self, board_coord):
        if self.get_state() == "WaitingForMove":
            if self.model.is_cell_available_for_move(board_coord):
                num_cells_flipped = self.model.put_piece(board_coord)
                
                self.play_put_down_piece_sound(num_cells_flipped)

                do_end_game = False

                if self.model.can_toggle_current_player():
                    self.model.toggle_current_player()
                elif self.model.can_player_move(self.model.get_active_player_number()) == False:
                    do_end_game = True
                    
                self.view.update_from_model(self.model)
                
                if do_end_game:
                    self.set_state("EndGame")
                    
    def play_sound(self, sound_name):
        if self.sound_enable:
            if not self.sounds.has_key(sound_name):
                print "ReversiController.play_sound(\"%s\") - WARNING, sound does not exist!" % str(sound_name)
            else:
                sound = self.sounds[sound_name]
                sound.play()
    
    def play_put_down_piece_sound(self, num_cells_flipped):
        #possible_sound_names = ['putdownflip2', 'putdownflip3', 'putdownflip4', 'putdownflip5', 'putdownflip']

        sound_name = None
        if num_cells_flipped >= 0 and num_cells_flipped <= 2:
            possible_sound_names = ['putdownflip3', 'putdownflip']
            choice = random.randint(0, len(possible_sound_names)-1)
            sound_name = possible_sound_names[choice]
        else:
            sound_name = "putdownflip2"

#===============================================================================
#        if num_cells_flipped >= 0 and num_cells_flipped <= 4:
#            sound_name = "putdownflip3"
#        elif num_cells_flipped == 3:
#            sound_name = "putdownflip"
#===============================================================================
        
        self.play_sound(sound_name)
        
        #if num_cells_flipped >= 6:
        #    self.play_sound("clapping")

    def handle_restart_button_click(self):
        self.set_state("StartGame")
    
    def debug_make_move(self):
        #piece_color_name = self.model.
        #self.model.get_board_model().get_all_toggleable_cells()
        pass

    def set_player1_color(self, color):
        global WHITE
        WHITE = color
        self.view.update_from_model(self.model)

    def set_player2_color(self, color):
        global BLACK
        BLACK = color
        self.view.update_from_model(self.model)

    def set_line_color(self, color):
        global cell_padding_color
        cell_padding_color = color
        self.view.redraw_back()

    def set_back_color(self, color):
        global background_color
        background_color = color
        self.view.redraw_back()
        self.view.update_from_model(self.model)

    def set_board_color(self, color):
        global background_board_color
        background_board_color = color
        self.view.update_from_model(self.model)

    def set_current_player(self, player):
        if self.parent is not None:
            self.parent.set_current_player(player)

    def change_sound(self, sound):
        self.sound_enable = sound
        
    def run(self):
        global screen_size
        pygame.display.init()
        self.screen = pygame.display.get_surface()
        if not(self.screen):
            info = pygame.display.Info()
            screen_size = (info.current_w, info.current_h - 75)
            self.screen = pygame.display.set_mode(screen_size) #, pygame.FULLSCREEN)
            pygame.display.set_caption(_('Reversi'))
        screen_size = self.screen.get_size()

        # Init mixer
        self.use_sounds = True
        sound_info = None
        if pygame.mixer:
            pygame.mixer.init()
            #pygame.mixer.init(22050,-16,1,1024)
            sound_info = pygame.mixer.get_init()
            if sound_info:
                self.use_sounds = True
                print "sound_info = %s" % str(sound_info)
        
        # Load sounds
        if self.use_sounds:
            self.sounds = {}
            self.sounds["clapping"] = load_sound("clapping.ogg")
            self.sounds["putdownflip"] = load_sound("putdownflip.ogg")
            self.sounds["putdownflip2"] = load_sound("putdownflip2.ogg")
            self.sounds["putdownflip3"] = load_sound("putdownflip3.ogg")
            self.sounds["putdownflip4"] = load_sound("putdownflip4.ogg")
            self.sounds["putdownflip5"] = load_sound("putdownflip5.ogg")
            self.sounds["putdownflip5a"] = load_sound("putdownflip5a.ogg")
        
        # Create board view
        self.view = ReversiView(self, screen_size, (num_columns, num_rows))
        
        # Create board model
        self.model = ReversiModel(self, (num_columns, num_rows))
        
        # Setup start state
        self.set_state("StartGame")

        while True:
            # Process events
            while gtk.events_pending():
                gtk.main_iteration()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q and event.mod & pygame.KMOD_CTRL:
                        return
                    elif event.key == pygame.K_r: # and event.mod & pygame.KMOD_CTRL:
                        self.set_state("StartGame")
                    elif self.get_state() == "EndGame":
                        self.set_state("StartGame")
                        continue

                if self.view.handle_event(event):
                    continue
            
            # Draw
            self.view.draw(self.screen)
            pygame.display.flip()
            
            # Update clock
            self.clock.tick(10)



#===============================================================================
# main()
#===============================================================================

def main():
   
    # Create primary controller and launch it.
    primary_controller = ReversiController()
    primary_controller.run()

if __name__=="__main__":
    main()
