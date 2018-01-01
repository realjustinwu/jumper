from PIL import Image
import os
import time
import sys

SAME_COLOR_PRECISION = 20
CHESS_WIDTH = 10
RESIZE_WIDTH = 128
CHESS_COLOR_1 = (56, 59, 96)
CHESS_COLOR_2 = (63, 53, 83)
DURATION_DISTANCE_RATE = 11.32
WHITE_DOT_COLOR = (255, 255, 255)

def same_color(col1, col2):
    dr = col1[0] - col2[0]
    dg = col1[1] - col2[1]
    db = col1[2] - col2[2]
    return (dr*dr + dg*dg + db*db) ** 0.5 <= SAME_COLOR_PRECISION

def draw_point(image, xy, color, r):
    (center_x, center_y) = xy
    (width, height) = image.size
    (start_x, start_y) = (center_x-r, center_y-r)
    for i in range(start_x, center_x + r):
        for j in range(start_y, center_y + r):
            if i>=0 and i<width and j >=0 and j<height:
                image.putpixel((i, j), color)

def save_oper_image(image, footer, dest, step):
    draw_point(image, footer, (255,255,255), 1)
    draw_point(image, dest, (0,0,0), 1)
    image.save("oper_image_%d.png" % step)

def execute_adb(duration, p1, p2):
    event_string = "adb shell input swipe %d %d %d %d %d " % (p1[0], p1[1], p2[0], p2[1], duration)
    os.system(event_string)
    print ("adb shell sendevent duration: %d" % duration)

def load_screen():
    os.system("adb shell screencap -p | perl -pe 's/x0Dx0A/x0A/g' > screen.png")

class JumpTask(object):

    def __init__(self):
        self.source_image_size = None
        self.oper_image = None
        self.oper_image_width = RESIZE_WIDTH
        self.oper_image_height = None
        self.bg_color = None
        self.step_count = 0

    def execute(self):
        self.step_count += 1
        load_screen()
        self.load_and_get_sample("screen.png")
        self.get_bg_color()
        self.chess_footer_point = self.getChessFooterPoint()
        self.object_highest_point = self.getHighestObjectColorPoint()
        #print(self.object_highest_point)
        #print(self.chess_footer_point)
        if self.object_highest_point == None or self.chess_footer_point == None:
            raise Exception('cant find desttination or chess point')
        self.next_point = self.getNextStepPoint()
        self.duration = self.calculate_duration()
        save_oper_image(self.oper_image, self.chess_footer_point, self.next_point, self.step_count)
        execute_adb(self.duration, self.chess_footer_point, self.object_highest_point)

    def load_and_get_sample(self, iamge_path):
        image = Image.open(iamge_path)
        self.source_image_size = image.size
        (s_width, s_height) = image.size
        self.oper_image_height = s_height * self.oper_image_width / s_width
        self.oper_image = image.resize((self.oper_image_width, self.oper_image_height))

    def get_bg_color(self):
        self.bg_color = self.oper_image.getpixel((0, self.oper_image_width/2))
        #print(self.bg_color)

    def can_be_chess(self, p):
        x = p[0]
        chess_x = self.chess_footer_point[0]
        return x - chess_x <=CHESS_WIDTH and chess_x - x <=CHESS_WIDTH

    def getHighestObjectColorPoint(self):
        for y in range(self.oper_image_width/2, self.oper_image_height):
            for x in range(0, self.oper_image_width):
                cur_color = self.oper_image.getpixel((x, y))
                if not same_color(self.bg_color, cur_color) and not self.can_be_chess((x, y)):
                    r = x
                    for z in range(x + 1, self.oper_image_width):
                        nex_color = self.oper_image.getpixel((z, y))
                        if same_color(nex_color, self.bg_color):
                            break
                        r = z
                    return ((x + r) / 2, y + 2)
        return None

    def getChessFooterPoint(self):
        for y in range(self.oper_image_height-self.oper_image_width/3, 0, -1):
            for x in range(0, self.oper_image_width):
                cur_color = self.oper_image.getpixel((x, y))
                body_color = self.oper_image.getpixel((x, y-4))
                if same_color(CHESS_COLOR_1, cur_color) and same_color(CHESS_COLOR_2, body_color):
                    return (x + 2, y)
        return None

    def getNextStepPoint(self):
        (x, y) = self.object_highest_point
        highest_color = self.oper_image.getpixel(self.object_highest_point)
        y_b = y
        for i in range(y_b, y+30):
            cur_color = self.oper_image.getpixel((x, i))
            if same_color(highest_color, cur_color):
                y_b = i
            elif same_color(WHITE_DOT_COLOR, cur_color):
                continue
            else :
                break
        return (x, (y+y_b)/2)

    def calculate_duration(self):
        (x1, y1) = self.next_point
        (x2, y2) = self.chess_footer_point
        distance = ((x1 - x2)**2 + (y1 - y2)**2) ** 0.5
        print("distance:", distance)
        #print("duration:", (distance * DURATION_DISTANCE_RATE))
        return distance * DURATION_DISTANCE_RATE


def main():
    jumpTask = JumpTask()

    try:
        while True:
            jumpTask.execute()
            time.sleep(2)
    except Exception as e:
        print(e)
    
    #execute_adb(int(sys.argv[1]))
    #load_screen()

if __name__ == '__main__':
    main()



