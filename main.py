from js import document, Math, setInterval, window, clearInterval, requestAnimationFrame
from pyodide import create_proxy
from game_conv import GameOfLife
import math
import time


class CellType:
    RECT = 0,
    CIRCLE = 1


class GameManager:
    MAX_ZOOM = 2
    MIN_ZOOM = 0.125

    cell_size = 15
    board_width = 400
    board_height = 400

    cell_type = CellType.RECT
    SCROLL_SENSITIVITY = 0.0005

    dragStart_x = 0
    dragStart_y = 0

    isRunning = True
    forceRedraw = True

    isDragging = False
    isPinchZooming = False
    current_scale = 1
    dragStartPosition_x = 0
    dragStartPosition_y = 0
    currentTransformedCursor_x = 0
    currentTransformedCursor_y = 0

    # Touch handling
    touch_events = []
    prevDiff = -1

    alive_cells = []

    def __init__(self, ctx, canvas):
        self.ctx = ctx
        self.canvas = canvas
        self.resizeCanvas(None)
        self.start = time.time()

        self.board_width = int(window.innerWidth / self.cell_size)
        self.board_height = int(window.innerHeight / self.cell_size)

        # self.game = GameOfLife.from_random(self.board_width, self.board_height)
        self.game = GameOfLife.from_lif("breeder.lif")
        self.board_width, self.board_height = self.game.board.shape
        print(self.game.board.shape)
        # self.update_board()
        self.draw_board()

        self.ctx.translate(-(self.board_width * self.cell_size) / 2, -(self.board_height * self.cell_size) / 2)
        self.register_event_listeners()

    def register_event_listeners(self):
        self.interval_id = setInterval(create_proxy(self.update_board), 0.3)

        self.canvas.addEventListener('mouseup', create_proxy(self.onMouseUp))
        self.canvas.addEventListener('mousedown', create_proxy(self.onMouseDown))
        self.canvas.addEventListener('mousemove', create_proxy(self.onMouseMove))
        self.canvas.addEventListener('touchstart', create_proxy(self.onTouchStart))
        self.canvas.addEventListener('touchend', create_proxy(self.onTouchEnd))
        self.canvas.addEventListener('touchmove', create_proxy(self.onTouchMove))
        self.canvas.addEventListener('wheel', create_proxy(self.onWheel))
        window.addEventListener('keyup', create_proxy(self.handle_key))

    def pause(self, e=None):
        if self.isRunning:
            clearInterval(self.interval_id)
        else:
            self.interval_id = setInterval(
                create_proxy(self.update_board), 5)
        self.isRunning = not self.isRunning
        print(self.isRunning)

    def handle_key(self, e):
        if e.keyCode == 80:
            self.pause()
        elif e.keyCode == 83:
            self.update_board()
        elif e.keyCode == 49:
            self.cell_type = CellType.RECT
        elif e.keyCode == 50:
            self.cell_type = CellType.CIRCLE

    def update_board(self):
        self.game.step()
        self.forceRedraw = True
        self.alive_cells = self.game.get_alive_cells()
        self.draw_board()

    def draw_cell(self, x, y):
        if self.cell_type == CellType.RECT:
            self.ctx.fillRect(x, y, self.cell_size, self.cell_size)
        elif self.cell_type == CellType.CIRCLE:
            size = self.cell_size
            self.ctx.beginPath()
            self.ctx.arc(x + size/2, y + size/2, size/2, 0, 2 * Math.PI)
            self.ctx.fill()

    def draw_board(self, timestamp=None):
        requestAnimationFrame(create_proxy(self.draw_board))
        if not self.forceRedraw:  # or not self.isRunning:
            return
        offset_y = self.ctx.getTransform().f
        offset_x = self.ctx.getTransform().e
        self.ctx.save()
        self.ctx.setTransform(1, 0, 0, 1, 0, 0)

        self.ctx.clearRect(0, 0, self.canvas.width, self.canvas.height)
        self.ctx.fillStyle = "black"
        self.ctx.fillRect(0, 0, self.canvas.width, self.canvas.height)

        self.ctx.restore()

        self.ctx.lineWidth = 4
        self.ctx.strokeStyle = 'white'
        half_cell_size = self.cell_size / 2
        self.ctx.strokeRect(-half_cell_size,
                            -half_cell_size,
                            self.cell_size * self.board_width + half_cell_size,
                            self.cell_size * self.board_height + half_cell_size)

        board_offset_x_min = max(0, math.ceil(-offset_x / (self.cell_size * self.ctx.getTransform().a)))
        board_offset_x_max = min(self.board_width, math.ceil((self.canvas.width - offset_x) / (self.cell_size * self.ctx.getTransform().a)))

        board_offset_y_min = max(0, math.ceil(-offset_y / (self.cell_size * self.ctx.getTransform().a)))
        board_offset_y_max = min(self.board_height, math.ceil((self.canvas.height - offset_y) / (self.cell_size * self.ctx.getTransform().a)))

        for i, j in self.alive_cells:
            if i < board_offset_x_min or i > board_offset_x_max:
                continue

            if j < board_offset_y_min or j > board_offset_y_max:
                continue
            self.ctx.fillStyle = "#FFFFFF"
            self.draw_cell(i * self.cell_size,
                           j * self.cell_size)

        end = time.time()
        fps = 1.0 / ((end - self.start))
        # print("FPS: " + str(fps))
        self.start = end
        self.forceRedraw = False

    def resizeCanvas(self, e):
        self.canvas.width = window.innerWidth
        self.canvas.height = window.innerHeight

    def getTransformedPoint(self, x, y):
        transform = self.ctx.getTransform()
        inverseZoom = 1 / transform.a

        transformedX = inverseZoom * x - inverseZoom * transform.e
        transformedY = inverseZoom * y - inverseZoom * transform.f
        return transformedX, transformedY

    def onMouseDown(self, event):
        self.isDragging = True
        self.dragStartPosition_x, self.dragStartPosition_y = self.getTransformedPoint(event.offsetX, event.offsetY)

    def onMouseMove(self, event):
        self.currentTransformedCursor_x, self.currentTransformedCursor_y = self.getTransformedPoint(event.offsetX, event.offsetY)

        if self.isDragging:
            self.ctx.translate(self.currentTransformedCursor_x - self.dragStartPosition_x,
                               self.currentTransformedCursor_y - self.dragStartPosition_y)
            if not self.isRunning:
                self.forceRedraw = True
            # self.draw_board()

    def onMouseUp(self, event):
        self.isDragging = False

    def __set_ctx_scale(self, zoom):
        self.ctx.translate(self.currentTransformedCursor_x, self.currentTransformedCursor_y)
        self.ctx.scale(zoom, zoom)
        self.ctx.translate(-self.currentTransformedCursor_x, - self.currentTransformedCursor_y)

    def onWheel(self, event):
        scale = self.ctx.getTransform().d
        if (scale > self.MIN_ZOOM and event.deltaY >= 0):
            self.__set_ctx_scale(max(0.9, (self.MIN_ZOOM / scale)))
        if (scale < self.MAX_ZOOM and event.deltaY < 0):
            self.__set_ctx_scale(min(1.1, (self.MAX_ZOOM / scale)))

        if not self.isRunning:
            self.forceRedraw = True

        event.preventDefault()

    # Handle touch

    def onTouchStart(self, event):
        event.preventDefault()
        touches = event.changedTouches
        indexes = [i for i, ev in enumerate(self.touch_events) if ev.identifier == touches.item(0).identifier]
        if len(indexes) > 0:
            self.touch_events.pop(indexes[0])

        self.touch_events.append(touches.item(0))

        if len(self.touch_events) == 1:
            self.isDragging = True
            self.isPinchZooming = False
            self.dragStartPosition_x, self.dragStartPosition_y = self.getTransformedPoint(self.touch_events[0].pageX, self.touch_events[0].pageY)
        if len(self.touch_events) == 2:
            self.prevDiff = math.sqrt((self.touch_events[1].pageY - self.touch_events[0].pageY)**2 +
                                      (self.touch_events[1].pageX - self.touch_events[0].pageX)**2)
            self.isDragging = False
            self.isPinchZooming = True

    def onTouchMove(self, event):
        event.preventDefault()
        touches = event.changedTouches
        indexes = [i for i, ev in enumerate(self.touch_events) if ev.identifier == touches.item(0).identifier]
        if len(indexes) > 0:
            self.touch_events.pop(indexes[0])

        self.touch_events.append(touches.item(0))

        if self.isDragging:
            self.currentTransformedCursor_x, self.currentTransformedCursor_y = self.getTransformedPoint(self.touch_events[0].pageX, self.touch_events[0].pageY)
            self.ctx.translate(self.currentTransformedCursor_x - self.dragStartPosition_x,
                               self.currentTransformedCursor_y - self.dragStartPosition_y)
            self.dragStartPosition_x, self.dragStartPosition_y = self.getTransformedPoint(self.touch_events[0].pageX, self.touch_events[0].pageY)
            if not self.isRunning:
                self.forceRedraw = True
        elif self.isPinchZooming:
            self.currentTransformedCursor_x, self.currentTransformedCursor_y = self.getTransformedPoint(
                (self.touch_events[1].pageX + self.touch_events[0].pageX) / 2,
                (self.touch_events[1].pageY + self.touch_events[0].pageY) / 2
            )
            curDiff = math.sqrt((self.touch_events[0].pageY - self.touch_events[1].pageY)**2 + (self.touch_events[0].pageX - self.touch_events[1].pageX)**2)
            perc = (curDiff - self.prevDiff) / (math.sqrt(self.canvas.height**2 + self.canvas.width**2) / 6)
            scale = self.ctx.getTransform().d

            if curDiff > self.prevDiff:
                if (scale < self.MAX_ZOOM):
                    self.__set_ctx_scale(min(1 + perc, (self.MAX_ZOOM / scale)))
            if curDiff < self.prevDiff:
                if (scale > self.MIN_ZOOM):
                    self.__set_ctx_scale(max(1 + perc, (self.MIN_ZOOM / scale)))

            self.prevDiff = curDiff

    def onTouchEnd(self, event):
        event.preventDefault()
        indexes = [i for i, ev in enumerate(self.touch_events) if ev.identifier == event.changedTouches.item(0).identifier]
        if len(indexes) > 0:
            self.touch_events.pop(indexes[0])

        self.isDragging = False
        self.isPinchZooming = False


def main():
    canvas = document.getElementById("canvas")
    ctx = canvas.getContext("2d")

    GameManager(ctx, canvas)


if __name__ == "__main__":
    main()
