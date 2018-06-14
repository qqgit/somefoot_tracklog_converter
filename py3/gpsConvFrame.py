'''
Created on 2012-3-17

@author: cqq
'''
import wx
import wx.lib.filebrowsebutton as filebrowse
import os
import codecs
from subprocess import call
import time
import json

class gpsConvFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, "GPS Track Data Converter")
        panel = wx.Panel(self)
        
        # First create the controls
        # First create the controls
        #     native <--->ascii controls
        TitleLbl = wx.StaticText(panel, -1, "Response ---> plt")
        TitleLbl.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
       
        #         Response -->plt controls
        srcfbb = filebrowse.FileBrowseButton(
                                                panel, 
                                                -1, 
                                                size=(450, -1), 
                                                labelText="Response Source File:", 
                                                fileMask="*.txt",
                                                changeCallback = self.srcfbbCallback 
                                                )
        tgtLbl = wx.StaticText(panel, -1, "Target File:")
        tgtTxt = wx.TextCtrl(panel, -1, "")
        convertBtn = wx.Button(panel, -1, "Convert")
        self.Bind(wx.EVT_BUTTON, self.OnconvertBtnClick, convertBtn)
        
        # 
        self.srcfbb = srcfbb
        self.tgtTxt = tgtTxt
        self.convertBtn = convertBtn
        self.tgtRevFileName = None
        
        # Now do the layout.
        
        # mainSizer is the top-level one that manages everything
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        leftSizer = wx.BoxSizer(wx.VERTICAL)
        
        #    leftTopSizer is the sizer for native <---> ascii controls
        leftSizer.Add(TitleLbl, 0, wx.ALL, 5)
        leftSizer.Add(wx.StaticLine(panel), 0,
                      wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        
        
        leftSizer.Add(srcfbb, 0, wx.EXPAND)
        
        asctgtSizer = wx.BoxSizer(wx.HORIZONTAL)
        asctgtSizer.Add(tgtLbl, 0,
                        wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        asctgtSizer.Add(tgtTxt, 1, wx.EXPAND|wx.ALL)
        
        leftSizer.Add(asctgtSizer, 0, wx.EXPAND|wx.ALL, 10)
        
        convertBtnSizer = wx.BoxSizer(wx.HORIZONTAL)
        convertBtnSizer.Add((50,50))
        convertBtnSizer.Add(convertBtn, 1, wx.EXPAND)
        convertBtnSizer.Add((50,50))
        leftSizer.Add(convertBtnSizer, 0, wx.EXPAND|wx.ALL, 10)
        
        mainSizer.Add(leftSizer, 0, wx.EXPAND, 5)
        
        panel.SetSizer(mainSizer)
        
        # Fit the frame to the needs of the sizer. The frame will
        # automatically resize the panel as needed. Also prevent the
        # frame from getting smaller than this size.
        mainSizer.Fit(self)
        mainSizer.SetSizeHints(self)
        
    def srcfbbCallback(self, evt):
        srcFileStr = evt.GetString()
        # parse source file name and generate default target file name, 
        # then set it to target control 
        pathName,fileName = os.path.split(srcFileStr)
        fileNameTrunk, fileNameExt = os.path.splitext(fileName)
        tgtFileStr = os.path.join(pathName,fileNameTrunk+".plt")
        tgtRevFileStr = os.path.join(pathName,fileNameTrunk+"_reverse.plt")
        self.tgtRevFileName = tgtRevFileStr
        
        #tgtFileStr = srcFileStr
        self.tgtTxt.SetValue(tgtFileStr)
        
    def OnconvertBtnClick(self, evt):
        srcFileName = self.srcfbb.GetValue()
        tgtFileName = self.tgtTxt.GetValue()
        pathName,fileName = os.path.split(tgtFileName)
        fileNameTrunk, fileNameExt = os.path.splitext(fileName)
        #tgtRevFileName = os.path.join(pathName,fileNameTrunk+"_reverse.plt")
        #kmlFileName = os.path.join(pathName,fileNameTrunk+".kml")
        
        #check sourceFileName and read file contents
        if os.path.isfile(srcFileName) == False: 
            self.tgtTxt.SetValue(srcFileName + " does NOT exist!!!")
            return "File not exist!"
        fList = self.openAndReadSourceFile(srcFileName)
        print("after openAndReadSourceFile")

        if fList==None: 
            print("fList is None")
            self.tgtTxt.SetValue( "fList is NOT generated!!!")
        else:
            print("fList is not None")
            print(len(fList))
            fListRev=fList[::-1]
        self.writeTargetFile(tgtFileName, fList)
        #self.writeTargetFile(tgtRevFileName, fListRev)
        print("after writeTargetFile")
        self.writeKMLFile(srcFileName,tgtFileName)
        print("after writeKMLFile")
        if os.path.isfile(tgtFileName) == True: 
            self.tgtTxt.SetValue("plt file: %s has been created." % tgtFileName)
        kmlFile = tgtFileName.rstrip('.plt')+'.kml'
        if os.path.isfile(kmlFile) == True:
            self.tgtTxt.SetValue("kml file: %s has been created." % kmlFile)

        #check target filename
#         if os.path.isfile(tgtFileName) == False: 
#             self.tgtTxt.SetValue(tgtFileName + " is NOT generated!!!")
#             return "File not generated!"
#         try:
#             call(["notepad.exe", tgtFileName])
#         except IOError:
#             self.tgtTxt.SetValue("Error occured when open " + tgtFileName)
#             return "Error open target file"
    def openAndReadSourceFile(self,fName):
        '''
        Read "[[timeString,latitude,longitude,altitude,],...,[]]" format 
        source (response) file. fName should be
        full file names with directory.
        Parse the contents of source file to form a list.
        Return a list as specified in source file.
        '''
        if os.path.isfile(fName) == False: return "Not a file name!"
        #try to open file and evaluate its content to a list.
        try:
            f = codecs.open(fName,mode="r")
            try:
                fLn = f.readline()
            finally:    
                f.close() 
            #ecaluate fLns to Python list
            fList = eval(fLn)
            # i[1] : Latitude - decimal degrees. 
            # i[2] : Longitude - decimal degrees.
            # 0    : code - 0 if normal, 1 if break in track line
            # i[3] : Altitude in feet (-777 if not valid)  1 m = 3.28084feet 
            # i[0] : TDateTime - 0 is 12/30/1899 12:00 am, convert to TDateTime is dummy
            #fListResort = [[i[1],i[2],0,i[3]*3.28084,float(i[0])/40000.0] for i in fList]
            #resort elements of fList or return it directly.
            return fList
        except IOError:
            pass
    
    def writeTargetFile(self,fName=None, fList=None):
        '''
        write target file with properly file format. 
        write contents from list fList to file fName.
        format is: 
        Track File (.plt)

        Line 1 : File type and version information
        Line 2 : Geodetic Datum used for the Lat/Lon positions for each trackpoint
        Line 3 : "Altitude is in feet" - just a reminder that the altitude is always stored in feet
        Line 4 : Reserved for future use
        Line 5 : multiple fields as below
        
            Field 1 : always zero (0)
            Field 2 : width of track plot line on screen - 1 or 2 are usually the best
            Field 3 : track color (RGB)
            Field 4 : track description (no commas allowed)
            Field 5 : track skip value - reduces number of track points plotted, usually set to 1
            Field 6 : track type - 0 = normal , 10 = closed polygon , 20 = Alarm Zone
            Field 7 : track fill style - 0 =bsSolid; 1 =bsClear; 2 =bsBdiagonal; 3 =bsFdiagonal; 4 =bsCross;
            5 =bsDiagCross; 6 =bsHorizontal; 7 =bsVertical;
            Field 8 : track fill color (RGB)
        
        Line 6 : Number of track points in the track, not used, the number of points is determined when reading the points file
        
        Trackpoint data
        
            One line per trackpoint
            each field separated by a comma
            non essential fields need not be entered but comma separators must still be used (example ,,)
            defaults will be used for empty fields
        
        Field 1 : Latitude - decimal degrees.
        Field 2 : Longitude - decimal degrees.
        Field 3 : Code - 0 if normal, 1 if break in track line
        Field 4 : Altitude in feet (-777 if not valid)
        Field 5 : Date - see Date Format below, if blank a preset date will be used
        Field 6 : Date as a string
        Field 7 : Time as a string
        
        Note that OziExplorer reads the Date/Time from field 5, the date and time in fields 6 & 7 are ignored.
        
        Example
        -27.350436, 153.055540,1,-777,36169.6307194, 09-Jan-99, 3:08:14
        -27.348610, 153.055867,0,-777,36169.6307194, 09-Jan-99, 3:08:14 
        
        Date Format

        Delphi stores date and time values in the TDateTime type. The integral part of a TDateTime value is the number of days that have passed since 12/30/1899. The fractional part of a TDateTime value is the time of day.
        
        Following are some examples of TDateTime values and their corresponding dates and times:
        
        0 - 12/30/1899 12:00 am
        2.75 - 1/1/1900 6:00 pm
        -1.25 - 12/29/1899 6:00 am
        35065 - 1/1/1996 12:00 am 
        '''
        if fName == None: return "File name is empty!"
        #if os.path.isfile(fName) == False: return "Not a file name!"
        if fList == None: return "fList is empty!"

        print("fName in writeTargetFile is: " + fName)
#       parse absolute filename to path, name trunk and extension
        #pathName,fileName = os.path.split(fName)
        #fileNameTrunk, fileNameExt = os.path.splitext(fileName)
        #fileName2Write = os.path.join(pathName,fileNameTrunk+"_formated.plt")
        fileName2Write = fName
#       if sorted list of updated dict is exist, write it in "keyi = valuei" format  
        if fList != None:
            f = codecs.open(fileName2Write,mode="w")
            f.write("OziExplorer Track Point File Version 2.1\n")
            f.write("WGS 84\n")
            f.write("Altitude is in Feet\n")
            f.write("Reserved 3\n")
            f.write("0,2,255,ConvertedByQQ,0,0,2,8421376\n")
            f.write(str(len(fList)) + "\n")
            # i[1] : Latitude - decimal degrees. 
            # i[2] : Longitude - decimal degrees.
            # 0    : code - 0 if normal, 1 if break in track line
            # i[3] : Altitude in feet (-777 if not valid)  1 m = 3.28084feet 
            # i[0] : TDateTime - 0 is 12/30/1899 12:00 am, convert to TDateTime is dummy
            #[[i[1],i[2],0,i[3]*3.28084,float(i[0])/40000.0] for i in fList]
            for i in fList:
                f.write(str(i[1])+','+str(i[2])+',0,'+str(i[3]*3.28084)+','+str(float(i[0])/40000.0)+',,'+'\n')
            f.close()      

    def writeKMLFile(self,srcFileName=None, tgtFileName=None):
        '''
        write target file with properly file format. 
        write contents from list fList to file fName.
        format is: 
        Keyhole Markup Language (.kml)
        First, use Google Earth to draw a sketch and then save it as .kml file.
        Then, use the parser from pykml to parse the previous .kml file and 
        use the write_python_script_for_kml_document from pykml.factory to create script for it.
        Last, modify the script to adapt the usage here and write this function
        '''
        pathName,fileName = os.path.split(tgtFileName)
        fileNameTrunk, fileNameExt = os.path.splitext(fileName)
        kmlFileName = os.path.join(pathName,fileNameTrunk+".kml")
        
        #check sourceFileName and read file contents
        if os.path.isfile(srcFileName) == False: 
            self.tgtTxt.SetValue(srcFileName + " does NOT exist!!!")
            return "File not exist!"
        
        utf8_json_data = json.loads(open(srcFileName).read(),encoding='utf-8')
        
        if tgtFileName == None: return "File name is empty!"
        #if os.path.isfile(fName) == False: return "Not a file name!"
        if utf8_json_data == None: return "utf8_json_data is empty!"
        
        strList = ["%s,%s,%s" % (i[2],i[1],i[3]) for i in utf8_json_data]
        strCoords = " ".join(strList)

        print("kmlFileName in writeKMLFile is: " + kmlFileName)
        #pathName,fileName = os.path.split(kmlFileName)
        #fileNameTrunk, fileNameExt = os.path.splitext(fileName)
        
        from lxml import etree
        from pykml.factory import KML_ElementMaker as KML
#         from pykml.factory import ATOM_ElementMaker as ATOM
#         from pykml.factory import GX_ElementMaker as GX
        
        doc = KML.kml(
          KML.Document(
            KML.name(str(fileNameTrunk)+".kml"),
            KML.Placemark(
              KML.name(str(fileNameTrunk)),
              KML.LineString(
                KML.tessellate('1'),
                KML.coordinates(strCoords),
              ),
            ),
          ),
        )
        #print etree.tostring(etree.ElementTree(doc),pretty_print=True)
        #outfile = file(tgtFileName.rstrip('.plt')+'.kml','w')
        outfile = open(kmlFileName,'w') # there is no file function in python3, use open instead.
        outfile.write(etree.tostring(doc, encoding='UTF-8', xml_declaration=True, pretty_print=True))
        
if __name__ == '__main__':        
#     app = wx.PySimpleApp()
    app = wx.App()
    gpsConvFrame().Show()
    app.MainLoop()
            