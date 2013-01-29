#!python

# Load libraries
import wx
import libPipeline
import shlex
import re
import subprocess
import sys, os

def generalError(parent, msg):
    '''
    Function to present file not found error message
    '''
    error = wx.MessageDialog(parent, "Error -- %s" % msg)
    error.ShowModal()
    del error

def fileNotFoundError(parent, path):
    '''
    Function to present file not found error message
    '''
    error = wx.MessageDialog(parent, "Error -- %s not found" % path)
    error.ShowModal()
    del error
    
def normalizePaths(*args):
    '''
    Function to normalize arbitrary number of paths to OS convention
    '''
    if len(args) > 1:
        return tuple([os.path.abspath(path) for path in args])
    else:
        return os.path.abspath(args[0])

def wrapQuotes(*args):
    '''
    Function to wrap path names in quotes to avoid issues with special
    characters
    '''
    if len(args) > 1:
        return tuple('"' + path + '"' for path in args)
    else:
        return '"' + args[0] + '"'

class TabPanel(wx.Panel):
    """
    Class for individual tabs of notebook
    """
    def __init__(self, parent):
        """"""
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        
class OptionsPanel(wx.Panel):
    """
    Class for aligned options fields
    """
    def __init__(self, parent):
        """"""
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        sizer = wx.FlexGridSizer(cols=2)
        self.SetSizer(sizer)
        
        self.labelDict = {}
        self.fieldDict = {}
    
    def addField(self, fieldName, multiline=False, textSize=wx.Size(400,-1)):
        if fieldName in self.fieldDict.keys():
            generalError(self, "%s is duplicate field" % fieldName)
        else:
            # Setup label
            self.labelDict[fieldName] = wx.StaticText(self, 0)
            self.labelDict[fieldName].SetLabel(fieldName)
            self.GetSizer().Add(self.labelDict[fieldName], 0)
            
            # Setup text-entry field
            if multiline:
                self.fieldDict[fieldName] = wx.TextCtrl(self, wx.ID_ANY,
                                                        style=wx.TE_MULTILINE,
                                                        size=textSize)
            else:
                self.fieldDict[fieldName] = wx.TextCtrl(self, wx.ID_ANY,
                                                        size=textSize)
            self.GetSizer().Add(self.fieldDict[fieldName], 0)
    
    def addToParent(self, align=0, border=0):
        if not self.GetParent() is None:
            self.GetParent().Sizer.Add(self, 0, align, border)
        else:
            print >> sys.stderr, "No parent window found"
    
    def getFieldValue(self, fieldName):
        if fieldName in self.fieldDict.keys():
            return self.fieldDict[fieldName].GetValue()
        else:
            return None

class FileFieldPanel(wx.Panel):
    """
    Class for labeled file-browsing fields with common dialog and label
    """
    def __init__(self, parent, fieldNameList, add=True,
                 textSize=wx.Size(400,28), align=0, border=0):
        # Initialize from parent class
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        
        # Save field names & alignment
        self.fieldNameList = fieldNameList
        self.align = align
        self.border = border
        
        # Setup sizer
        sizer = wx.FlexGridSizer(cols=3)
        self.SetSizer(sizer)
        
        # Setup fields
        self.fieldDict = {}
        for fieldName in self.fieldNameList:
            self.fieldDict[fieldName] = FileField(self, fieldName, textSize)
            self.fieldDict[fieldName].addToParent()
        
        if add:
            self.addToParent()
    
    def addToParent(self):
        if not self.GetParent() is None:
            self.GetParent().Sizer.Add(self, 0, self.align, self.border)
        else:
            print >> sys.stderr, "No parent window found"
    
    def getFieldValue(self, fieldName):
        if fieldName in self.fieldDict.keys():
            return self.fieldDict[fieldName].textInput.GetValue()
        else:
            return None

class FileField():
    """
    Utility class to store individual fields for file information, consisting
    of label, text control, and browse button
    """
    def __init__(self, parent, fieldName, textSize=wx.Size(400,28)):
        self.parent = parent
        # Setup label
        self.fieldLabel = wx.StaticText(parent, wx.ID_ANY)
        self.fieldLabel.SetLabel(fieldName)
        
        # Setup text control for manual input
        self.textInput = wx.TextCtrl(parent, wx.ID_ANY, "", size=textSize)
        
        # Setup "Browse" button
        self.browseButton = wx.Button(parent, wx.ID_ANY, "Browse")
        
        # Setup event handler for browseButton
        parent.Bind(wx.EVT_BUTTON, self.browseForFile, self.browseButton)
    
    def addToParent(self):
        """
        Add to parent sizer
        """
        self.parent.GetSizer().Add(self.fieldLabel, 0,
                                   wx.ALIGN_CENTER_VERTICAL)
        self.parent.GetSizer().Add(self.textInput, 0,
                                   wx.ALIGN_CENTER_VERTICAL)
        self.parent.GetSizer().Add(self.browseButton, 0,
                                   wx.ALIGN_CENTER_VERTICAL)
    
    def browseForFile(self, event):
        dialog = wx.FileDialog(self.parent,
                               style=wx.FD_OPEN)
        dialog.ShowModal()
        self.textInput.SetValue( dialog.GetPath() )
        
class TabConvert(TabPanel):
    def __init__(self, parent, statusBar=None):
        # Run parent constructor
        TabPanel.__init__(self, parent)
        
        # Add description
        self.description = "Convert Illumina data to FASTQ format"
        self.tabDescription = wx.StaticText(self, wx.ID_ANY)
        self.tabDescription.SetLabel(self.description)
        self.GetSizer().Add(self.tabDescription, 0,
                            wx.ALIGN_CENTER | wx.ALIGN_TOP | wx.ALL,
                            10)
        
        # Add file fields
        self.fieldPanel = FileFieldPanel(self,
                                         ["Illumina File", "FASTQ File"],
                                         add=True)
        
        # Add run button
        self.runButton = wx.Button(self, wx.ID_ANY, "&Run",
                                   style=wx.BU_EXACTFIT)
        self.GetSizer().Add(self.runButton, 0,
                            wx.ALIGN_BOTTOM | wx.ALIGN_CENTER)
        self.Bind(wx.EVT_BUTTON, self.run, self.runButton)
        
        if statusBar is None:
            # Add status bar
            self.statusBar = wx.StatusBar(self)
            self.GetSizer().Add(self.statusBar, 0, wx.ALIGN_BOTTOM)
        else:
            self.statusBar = statusBar
    
    def run(self, event):
        # Get file paths
        illuminaPath    = self.fieldPanel.getFieldValue("Illumina File")
        fastqPath       = self.fieldPanel.getFieldValue("FASTQ File")
        
        # Normalize paths
        illuminaPath, fastqPath = normalizePaths(illuminaPath,
                                                 fastqPath)
        
        # Attempt to open files
        try:
            illuminaFile = open(illuminaPath, "rb")
        except:
            fileNotFoundError(self, illuminaPath)
            return
        
        try:
            fastqFile = open(fastqPath, "wb")
        except:
            fileNotFoundError(self, fastqPath)
            return
        
        # Set status message
        self.statusBar.SetStatusText("Running")
        
        # Run conversion
        libPipeline.convertIlluminaToFASTQ(illuminaFile, fastqFile)
        
        # Close files
        illuminaFile.close()
        fastqFile.close()
        
        # Set status message
        self.statusBar.SetStatusText("Done")

class TabRunBowtie(TabPanel):
    # Set class constants
    BOWTIE_DEFAULT_OPTIONS = """
        --solexa1.3-quals -q \
        -n 2 --best -M 1 \
        -I 100 -X 300 \
        --threads 4
        """
    BOWTIE_DEFAULT_OPTIONS = ' '.join( BOWTIE_DEFAULT_OPTIONS.split('\n') )
    BOWTIE_DEFAULT_OPTIONS = ''.join( BOWTIE_DEFAULT_OPTIONS.split('\\') )
    BOWTIE_DEFAULT_OPTIONS = re.sub(r" +", ' ', BOWTIE_DEFAULT_OPTIONS)
    
    BOWTIE_CMD_PATTERN = "bowtie %(options)s %(index)s %(input)s"
    
    def __init__(self, parent, statusBar=None):
        # Run parent constructor
        TabPanel.__init__(self, parent)
        
        # Add description
        self.description = """
        Run Bowtie on paired- or single-end FASTQ data with given options
        """.strip()
        self.tabDescription = wx.StaticText(self, wx.ID_ANY)
        self.tabDescription.SetLabel(self.description)
        self.GetSizer().Add(self.tabDescription, 0,
                            wx.ALIGN_CENTER | wx.ALIGN_TOP | wx.ALL,
                            10)
        
        # Add file fields
        self.fieldPanel = FileFieldPanel(self,
                                         ("FASTQ File 1", "FASTQ File 2",
                                          "Index File (any)",
                                          "Alignments File", "Log File"),
                                         add=True)
        
        # Add checkbox for paired-end
        self.pairedEndLabel = wx.StaticText(self.fieldPanel, wx.ID_ANY,
                                            "Paired-End?")
        self.fieldPanel.GetSizer().Add(self.pairedEndLabel, 0)
        
        self.isPairedEnd = wx.CheckBox(self.fieldPanel, wx.ID_ANY)
        self.isPairedEnd.SetValue(True)
        self.fieldPanel.GetSizer().Add(self.isPairedEnd, 0)
        self.Bind(wx.EVT_CHECKBOX, self.switchPairedEnd, self.isPairedEnd)
        
        # Add text fields to get options for Bowtie
        self.optionsPanel = OptionsPanel(self)
        
        self.optionsPanel.addField("Bowtie Options", multiline=True)
        self.optionsPanel.fieldDict["Bowtie Options"
                                    ].SetValue(self.BOWTIE_DEFAULT_OPTIONS)
        
        self.optionsPanel.addToParent(align=wx.TOP, border=15)
        
        # Add run button
        self.runButton = wx.Button(self, wx.ID_ANY, "&Run",
                                   style=wx.BU_EXACTFIT)
        self.GetSizer().Add(self.runButton, 0,
                            wx.ALIGN_BOTTOM | wx.ALIGN_CENTER)
        self.Bind(wx.EVT_BUTTON, self.run, self.runButton)
        
        if statusBar is None:
            # Add status bar
            self.statusBar = wx.StatusBar(self)
            self.GetSizer().Add(self.statusBar, 0, wx.ALIGN_BOTTOM)
        else:
            self.statusBar = statusBar
            
    def switchPairedEnd(self, event):
        """
        Switch editability and appearance of FASTQ File 2 field when
        single vs. paried-end is toggled; retain field value
        """
        fastq2Input = self.fieldPanel.fieldDict["FASTQ File 2"].textInput
        if not self.isPairedEnd.GetValue():
            fastq2Input.SetEditable(False)
            fastq2Input.SetBackgroundColour("Gray")
        else:
            fastq2Input.SetEditable(True)
            fastq2Input.SetBackgroundColour(wx.NullColor)
    
    def run(self, event):
        """
        Run Bowtie on given files with given options
        """
        # Get file paths
        fastq1Path  = self.fieldPanel.getFieldValue("FASTQ File 1")
        fastq2Path  = self.fieldPanel.getFieldValue("FASTQ File 2")
        outPath     = self.fieldPanel.getFieldValue("Alignments File")
        logPath     = self.fieldPanel.getFieldValue("Log File")
        indexPath   = self.fieldPanel.getFieldValue("Index File (any)")
        
        # Normalize paths
        fastq1Path, fastq2Path      = normalizePaths(fastq1Path, fastq2Path)
        outPath, logPath, indexPath = normalizePaths(outPath, logPath,
                                                     indexPath)
        fastq1Path, fastq2Path = wrapQuotes(fastq1Path, fastq2Path)
        
        # Open output files
        try:
            outFile = open(outPath, "wb")
        except:
            fileNotFoundError(self, outPath)
        
        try:
            logFile = open(logPath, "wb")
        except:
            fileNotFoundError(self, logPath)
        
        # Get options
        isPairedEnd     = self.isPairedEnd.GetValue()
        bowtieOptions   = self.optionsPanel.getFieldValue("Bowtie Options")
        
        # Clean options
        bowtieOptions   = ' '.join(bowtieOptions.split('\n'))
        bowtieOptions   = ' '.join(bowtieOptions.split('\\'))
        
        indexBase       = re.match(
                                r"(.*?)(\.rev)?(\.[0-9]+)?(\.[a-zA-Z]*)?$",
                                indexPath)
        indexBase       = indexBase.group(1)
        indexBase       = wrapQuotes(indexBase)
        
        # Build shell command to execute
        
        # Input part
        if isPairedEnd:
            inputString = "-1 %s -2 %s" % (fastq1Path, fastq2Path)
        else:
            inputString = fastq1Path
        
        cmdString = self.BOWTIE_CMD_PATTERN % {"options"    : bowtieOptions,
                                               "index"      : indexBase,
                                               "input"      : inputString}
        
        # Parse command for subprocess
        cmdParsed = shlex.split(cmdString.encode("ascii"),
                                posix=(os.name=='posix'))
        print cmdString
        print cmdParsed
        
        # Set status message
        self.statusBar.SetStatusText("Running")
        
        # Run Bowtie
        bowtie      = subprocess.Popen(cmdParsed, stdout=outFile,
                                       stderr=logFile)
        exitStatus  = bowtie.wait()
        
        # Close output files
        outFile.close()
        logFile.close()
        
        # Set status message
        if exitStatus==0:
            self.statusBar.SetStatusText("Done")
        else:
            self.statusBar.SetStatusText("Error in Bowtie run -- check log")

class TabSummarizeAlignments(TabPanel):
    def __init__(self, parent, statusBar=None):
        # Run parent constructor
        TabPanel.__init__(self, parent)
        
        # Add description
        self.description = "Summarize paired-end alignments from Bowtie"
        self.tabDescription = wx.StaticText(self, wx.ID_ANY)
        self.tabDescription.SetLabel(self.description)
        self.GetSizer().Add(self.tabDescription, 0,
                            wx.ALIGN_CENTER | wx.ALIGN_TOP | wx.ALL,
                            10)
        
        # Add file fields
        self.fieldPanel = FileFieldPanel(self,
                                         ["Alignments File",
                                          "Read Summary File"],
                                         add=True)
        
        # Add checkbox for paired-end
        self.pairedEndLabel = wx.StaticText(self.fieldPanel, wx.ID_ANY,
                                            "Paired-End?")
        self.fieldPanel.GetSizer().Add(self.pairedEndLabel, 0)
        
        self.isPairedEnd = wx.CheckBox(self.fieldPanel, wx.ID_ANY)
        self.isPairedEnd.SetValue(True)
        self.fieldPanel.GetSizer().Add(self.isPairedEnd, 0)
        
        # Add run button
        self.runButton = wx.Button(self, wx.ID_ANY, "&Run",
                                   style=wx.BU_EXACTFIT)
        self.GetSizer().Add(self.runButton, 0,
                            wx.ALIGN_BOTTOM | wx.ALIGN_CENTER)
        self.Bind(wx.EVT_BUTTON, self.run, self.runButton)
        
        if statusBar is None:
            # Add status bar
            self.statusBar = wx.StatusBar(self)
            self.GetSizer().Add(self.statusBar, 0, wx.ALIGN_BOTTOM)
        else:
            self.statusBar = statusBar
    
    def run(self, event):
        # Get file paths
        alignmentsPath  = self.fieldPanel.getFieldValue("Alignments File")
        outPath         = self.fieldPanel.getFieldValue("Read Summary File")
        pairedEnd       = self.isPairedEnd.GetValue()
        
        # Normalize paths
        alignmentsPath, outPath = normalizePaths(alignmentsPath, outPath)
        
        # Attempt to open files
        try:
            alignmentsFile = open(alignmentsPath, "rb")
        except:
            fileNotFoundError(self, alignmentsPath)
            return
        
        try:
            outFile = open(outPath, "wb")
        except:
            fileNotFoundError(self, outPath)
            return
        
        # Set status message
        self.statusBar.SetStatusText("Running")
        
        # Summarize Bowtie output
        libPipeline.processBowtieOutput(alignmentsFile, outFile, pairedEnd)
        
        # Close files
        alignmentsFile.close()
        outFile.close()
        
        # Set status message
        self.statusBar.SetStatusText("Done")

class TabReadsToCounts(TabPanel):
    def __init__(self, parent, statusBar=None):
        # Run parent constructor
        TabPanel.__init__(self, parent)
        
        # Add description
        self.description = "Count read centers by base-pair for each chromosome"
        self.tabDescription = wx.StaticText(self, wx.ID_ANY)
        self.tabDescription.SetLabel(self.description)
        self.GetSizer().Add(self.tabDescription, 0,
                            wx.ALIGN_CENTER | wx.ALIGN_TOP | wx.ALL,
                            10)
        
        # Add file fields
        self.fieldPanel = FileFieldPanel(self,
                                         ["Read Summary File",
                                          "Chromosome Counts File"],
                                         add=True)
        
        # Add options
        self.randomizeLabel = wx.StaticText(self.fieldPanel, wx.ID_ANY,
                                            "Randomize ambiguous\ncenters?")
        self.fieldPanel.GetSizer().Add(self.randomizeLabel, 0)
        
        self.isRandomize = wx.CheckBox(self.fieldPanel, wx.ID_ANY)
        self.isRandomize.SetValue(True)
        self.fieldPanel.GetSizer().Add(self.isRandomize, 0)
        
        # Add run button
        self.runButton = wx.Button(self, wx.ID_ANY, "&Run",
                                   style=wx.BU_EXACTFIT)
        self.GetSizer().Add(self.runButton, 0,
                            wx.ALIGN_BOTTOM | wx.ALIGN_CENTER)
        self.Bind(wx.EVT_BUTTON, self.run, self.runButton)
        
        if statusBar is None:
            # Add status bar
            self.statusBar = wx.StatusBar(self)
            self.GetSizer().Add(self.statusBar, 0, wx.ALIGN_BOTTOM)
        else:
            self.statusBar = statusBar
    
    def run(self, event):
        # Get file paths
        readsPath   = self.fieldPanel.getFieldValue("Read Summary File")
        outPath     = self.fieldPanel.getFieldValue("Chromosome Counts File")
        
        # Normalize paths
        readsPath, outPath  = normalizePaths(readsPath, outPath)
        
        # Attempt to open files
        try:
            readsFile = open(readsPath, "rb")
        except:
            fileNotFoundError(self, readsPath)
            return
        
        try:
            outFile = open(outPath, "wb")
        except:
            fileNotFoundError(self, outPath)
            return
        
        # Set status message
        self.statusBar.SetStatusText("Running")
        
        # Convert reads to counts by bp
        libPipeline.readsToCounts(readsFile, outFile,
                                  self.isRandomize.GetValue())
        
        # Close files
        readsFile.close()
        outFile.close()
        
        # Set status message
        self.statusBar.SetStatusText("Done")

class TabReadLengthDist(TabPanel):
    def __init__(self, parent, statusBar=None):
        # Run parent constructor
        TabPanel.__init__(self, parent)
        
        # Add description
        self.description = "Tabulate distribution of fragment lengths"
        self.tabDescription = wx.StaticText(self, wx.ID_ANY)
        self.tabDescription.SetLabel(self.description)
        self.GetSizer().Add(self.tabDescription, 0,
                            wx.ALIGN_CENTER | wx.ALIGN_TOP | wx.ALL,
                            10)
        
        # Add file fields
        self.fieldPanel = FileFieldPanel(self,
                                         ["Read Summary File",
                                          "Fragment Length Dist. File"],
                                         add=True)
        
        # Add run button
        self.runButton = wx.Button(self, wx.ID_ANY, "&Run",
                                   style=wx.BU_EXACTFIT)
        self.GetSizer().Add(self.runButton, 0,
                            wx.ALIGN_BOTTOM | wx.ALIGN_CENTER)
        self.Bind(wx.EVT_BUTTON, self.run, self.runButton)
        
        if statusBar is None:
            # Add status bar
            self.statusBar = wx.StatusBar(self)
            self.GetSizer().Add(self.statusBar, 0, wx.ALIGN_BOTTOM)
        else:
            self.statusBar = statusBar
    
    def run(self, event):
        # Get file paths
        readsPath  = self.fieldPanel.getFieldValue("Read Summary File")
        outPath    = self.fieldPanel.getFieldValue("Fragment Length Dist. File")
        
        # Normalize paths
        readsPath, outPath  = normalizePaths(readsPath, outPath)
        
        # Attempt to open files
        try:
            readsFile = open(readsPath, "rb")
        except:
            fileNotFoundError(self, readsPath)
            return
        
        try:
            outFile = open(outPath, "wb")
        except:
            fileNotFoundError(self, outPath)
            return
        
        # Set status message
        self.statusBar.SetStatusText("Running")
        
        # Tabulate length distribution
        libPipeline.getReadLengthDist(readsFile, outFile)
        
        # Close files
        readsFile.close()
        outFile.close()
        
        # Set status message
        self.statusBar.SetStatusText("Done")


class NotebookPanel(wx.Notebook):
    """
    Class for notebook environment
    """
    def __init__(self,parent, statusBar=None):
        # Save status bar object
        self.statusBar = statusBar
        
        # Setup notebook
        wx.Notebook.__init__(self, parent, id=wx.ID_ANY, style=
                             wx.BK_DEFAULT
                             #wx.BK_TOP 
                             #wx.BK_BOTTOM
                             #wx.BK_LEFT
                             #wx.BK_RIGHT
                             )
        
        self.tabConvert     = TabConvert(self, statusBar = statusBar)
        self.tabBowtie      = TabRunBowtie(self, statusBar = statusBar)
        self.tabSummarize   = TabSummarizeAlignments(self, statusBar=statusBar)
        self.tabReadsToCounts = TabReadsToCounts(self, statusBar = statusBar)
        self.tabLengthDist  = TabReadLengthDist(self, statusBar = statusBar)
        
        self.AddPage(self.tabConvert, "Convert")
        self.AddPage(self.tabBowtie, "Run Bowtie")
        self.AddPage(self.tabSummarize, "Summarize Alignments")
        self.AddPage(self.tabReadsToCounts, "Count Reads per bp")
        self.AddPage(self.tabLengthDist, "Tabulate Fragment Lengths")
        
        self.Layout()
        self.Show()

class AppFrame(wx.Frame):
    """
    Frame that holds all other widgets
    """
    COPYRIGHT_TXT = "Copyright Alexander W. Blocker, 2011"
    
    def __init__(self):
        """Constructor"""
        wx.Frame.__init__(self, None, wx.ID_ANY,
                          "Illumina -> Bowtie -> Data Pipeline",
                          size=(800,500)
                          )
        panel = wx.Panel(self)
        self.CreateStatusBar()
        
        notebook = NotebookPanel(panel, statusBar=self.GetStatusBar())
        self.copyrightMsg = wx.StaticText(panel, wx.ID_ANY, self.COPYRIGHT_TXT)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(notebook, 1, wx.ALL|wx.EXPAND, 5)
        sizer.Add(self.copyrightMsg, 0,
                  wx.ALIGN_BOTTOM | wx.ALIGN_RIGHT | wx.ALL,
                  5)
        
        panel.SetSizer(sizer)
        self.Layout()

        self.Show()
        
        # Hack to make notebook draw properly on Windows
        self.SetSize(wx.Size(800,499))
        self.SetSize(wx.Size(800,500))

if __name__ == "__main__":
    # Run GUI application
    app = wx.PySimpleApp()
    frame = AppFrame()
    app.MainLoop()
