from math import *
import sys

class GCodeContext:
    def __init__(self, xy_feedrate, z_feedrate, start_delay, stop_delay, pen_up_angle, pen_down_angle, z_height, finished_height, x_home, y_home, register_pen, num_pages, continuous, file):
      self.xy_feedrate = xy_feedrate
      self.z_feedrate = z_feedrate
      self.start_delay = start_delay
      self.stop_delay = stop_delay
      self.pen_up_angle = pen_up_angle
      self.pen_down_angle = pen_down_angle
      self.z_height = z_height
      self.finished_height = finished_height
      self.x_home = x_home
      self.y_home = y_home
      self.register_pen = register_pen
      self.num_pages = num_pages
      self.continuous = continuous
      self.file = file
      
      self.drawing = False
      self.last = None

      self.preamble = [
        "(Scribbled version of %s @ %.2f)" % (self.file, self.xy_feedrate),
        "( %s )" % " ".join(sys.argv),
        "G21 (metric ftw)",
	"G1 X%.2f Y%.2f Z%0.2f (home)" % (self.x_home, self.y_home, self.finished_height),
	"",
	"(Pen Calibration Routine)",
	"",
	"G1 X%.2f Y%.2f Z%.2f (pen up)" % (self.x_home, self.y_home, self.pen_up_angle),
	"G1 X%.2f Y%.2f Z%.2f (pen down)" % (self.x_home, self.y_home, self.pen_down_angle),
	"G1 X%.2f Y%.2f Z%.2f (pen up)" % (self.x_home, self.y_home, self.pen_up_angle),
        ""
      ]

      self.postscript = [
        "",
				"(end of print job)",
				"G1 Z%0.2F (go up to finished level)" % self.finished_height,
				#"G4 P%d (wait %dms)" % (self.stop_delay, self.stop_delay), #Add this once Staubli supports wait commands
				#"M300 S255 (turn off servo)", #Add this once staubli supports enable and disable power through gcode
				#"G1 F%0.2F" % self.xy_feedrate, #Add this once staubli supports set speed by gcode
				"G1 X%0.2F Y%0.2F Z%0.2F (go home)" % (self.x_home, self.y_home, self.finished_height),
				#"M18 (drives off)",
      ]

      self.registration = [
        "(Self Registration is not supportted by Staubli yet)",
        #"M300 S%d (pen down)" % (self.pen_down_angle),
        #"G4 P%d (wait %dms)" % (self.start_delay, self.start_delay),
        #"M300 S%d (pen up)" % (self.pen_up_angle),
        #"G4 P%d (wait %dms)" % (self.stop_delay, self.stop_delay),
        #"M18 (disengage drives)",
        #"M01 (Was registration test successful?)",
        #"M17 (engage drives if YES, and continue)",
        ""
      ]

      self.sheet_header = [
        "(start of sheet header)",
        "G92 X%.2f Y%.2f Z%.2f (you are here)" % (self.x_home, self.y_home, self.z_height),
      ]
      if self.register_pen == 'true':
        self.sheet_header.extend(self.registration)
      self.sheet_header.append("(end of sheet header)")

      self.sheet_footer = [
        "(Start of sheet footer.)",
        "M300 S%d (pen up)" % (self.pen_up_angle),
        "G4 P%d (wait %dms)" % (self.stop_delay, self.stop_delay),
        "G91 (relative mode)",
        "G0 Z15 F%0.2f" % (self.z_feedrate),
        "G90 (absolute mode)",
        "G0 X%0.2f Y%0.2f F%0.2f" % (self.x_home, self.y_home, self.xy_feedrate),
        "M01 (Have you retrieved the print?)",
        "(machine halts until 'okay')",
        "G4 P%d (wait %dms)" % (self.start_delay, self.start_delay),
        "G91 (relative mode)",
        "G0 Z-15 F%0.2f (return to start position of current sheet)" % (self.z_feedrate),
        "G0 Z-0.01 F%0.2f (move down one sheet)" % (self.z_feedrate),
        "G90 (absolute mode)",
        "M18 (disengage drives)",
        "(End of sheet footer)",
      ]

      self.loop_forever = [ "M30 (Plot again?)" ]

      self.codes = []

    def generate(self):
      if self.continuous == 'true':
        self.num_pages = 1

      codesets = [self.preamble]
      if (self.continuous == 'true' or self.num_pages > 1):
        codesets.append(self.sheet_header)
      elif self.register_pen == 'true':
        codesets.append(self.registration)
      codesets.append(self.codes)
      if (self.continuous == 'true' or self.num_pages > 1):
        codesets.append(self.sheet_footer)

      if self.continuous == 'true':
        codesets.append(self.loop_forever)
        for codeset in codesets:
          for line in codeset:
            print line
      else:
        for p in range(0,self.num_pages):
          for codeset in codesets:
            for line in codeset:
              print line
          for line in self.postscript:
            print line

    def start(self):
      self.codes.append("G1 Z%0.2F (pen down)" % self.pen_down_angle)
      #self.codes.append("G4 P%d (wait %dms)" % (self.start_delay, self.start_delay))
      self.drawing = True

    def stop(self):
      self.codes.append("G1 Z%0.2F (pen up)" % self.pen_up_angle)
      #self.codes.append("G4 P%d (wait %dms)" % (self.stop_delay, self.stop_delay))
      self.drawing = False

    def go_to_point(self, x, y, stop=False):
      if self.last == (x,y):
        return
      if stop:
        return
      else:
        if self.drawing: 
            self.codes.append("G1 Z%0.2F (pen up)"  % self.pen_up_angle) 
            #self.codes.append("G4 P%d (wait %dms)" % (self.stop_delay, self.stop_delay))
            self.drawing = False
        self.codes.append("G1 X%.2f Y%.2f" % (x,y)
      self.last = (x,y)
	
    def draw_to_point(self, x, y, stop=False):
      if self.last == (x,y):
          return
      if stop:
        return
      else:
        if self.drawing == False:
            self.codes.append("G1 Z%0.2F (pen down)" % self.pen_down_angle)
            #self.codes.append("G4 P%d (wait %dms)" % (self.start_delay, self.start_delay))
            self.drawing = True
        self.codes.append("G1 X%.2f Y%.2f" % (x,y)
      self.last = (x,y)
