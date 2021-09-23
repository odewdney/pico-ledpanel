from machine import Pin
from rp2 import PIO, StateMachine, asm_pio, asm_pio_encode
from framebuf import FrameBuffer
import array
import struct
from dma import DmaChannel

HEIGHT=2

class LedPanel:
    """Led Panel controller"""
    COLOUR_DEPTH=4
    ROWS=4
    HEIGHT=2
    
    def __init__(self):
#        self.d1 = Pin(5,Pin.OUT)
#        self.d2 = Pin(6,Pin.OUT)
        self.data_pins = {}
        for hh in range(self.HEIGHT):
            for dd in range(2):
                dp = hh*2 + dd
                self.data_pins[dp] = Pin(5 + dp, Pin.OUT)
        self.a0 = Pin(0,Pin.OUT)
        self.a1 = Pin(1,Pin.OUT)
        self.oe = Pin(2,Pin.OUT, value=1)
        self.le = Pin(3,Pin.OUT)
        self.clk = Pin(4,Pin.OUT)
        self.le.off()
        # oe le a0 a1 clk
        self.data = array.array('I', (0 for i in range(24*self.ROWS*self.COLOUR_DEPTH*self.HEIGHT)))

    def start(self):
        first_data_pin = self.data_pins[0]
        self.sm = StateMachine(0, self.writedata, freq=8000000, sideset_base=self.oe, out_base=first_data_pin, set_base=self.a0)
        self.sm.active(1)
        self.sm.exec("set(y,15)")
    
    def end(self):
        self.sm.active(0)
        
# side_set = oe, le, clk
# set = a0, a1
# out=d1,d2,...
    @asm_pio(sideset_init=(PIO.OUT_LOW,)*3, out_init=(PIO.OUT_LOW,PIO.OUT_LOW)*2, set_init=(PIO.OUT_LOW,PIO.OUT_LOW), autopull=True, autopush=False, out_shiftdir=PIO.SHIFT_RIGHT, in_shiftdir=PIO.SHIFT_LEFT)
    def writedata():
        HEIGHT=2
        wrap_target()
        label("next")
        jmp(y_dec,"start")
        label("start")
    # load x = 384
        set(x,3)
        mov(isr,x)
        in_(null,7)
        mov(x,isr)
        jmp(x_dec,"row")

        label("row")
        out(pins,2*HEIGHT).side(0)
        jmp(x_dec, "row").side(4) # sideset clk
        
        # set A0-1
        set(x,15).side(0) # sideset pulse oe->high le->high 
        mov(isr,x).side(1) # set op + sideset_opt
        in_(null,10).side(3) # oe->low le->low clk->low
        mov(x,invert(y)).side(1)
        in_(x,2) # a0-1
        mov(exec,isr)

        # calc delay
        mov (isr,reverse(y))
        in_( null,2)
        mov( x,reverse(isr))
        in_ (null,32)
        in_( x,2)
        mov( x,isr)

        jmp(x_dec,"isdelay1") # jmp if 123
        jmp("next") # delay 0
        label("isdelay1")
        jmp(x_dec,"isdelay2") # jmp if 23
        set(x,4) # delay 1 + 2
        label("isdelay2")
        jmp(x_dec,"isdelay3") # jmp if 3 or delay2(5->4)
        set(x,6) # delay 2 + 1
        label("isdelay3")
        jmp(x_dec,"delaystart") # jmp if delay2(4->3) or delay2(10->9)
        set(x,11)

        label("delaystart")
        mov(isr,x)
        in_(null,9)
        mov(x,isr)

        label("delay")
        jmp(x_dec,"delay")

    # back to start
        wrap()

    def putData(self):
        self.sm.put(self.data)

    @micropython.viper
    def setpixel2(self, x : int,y : int,c : int):
        h = int(self.HEIGHT)
        bitoff = (((x&7) << 1) + ((y & 4) << 2)) * h + ((y & 8) >> 3)
        bitoff += (y>>4) << 1
        byteoff = (((y&3) * 24) + (((x & 0x38) >> 3) * 3 )) * h
        
        bitoff += byteoff << 5
        
        byteoff = bitoff >> 5
        bitoff = bitoff & 0x1f
        
        bit = 1 << bitoff
        nbit = (-1) ^ bit # = ~bit

        # bit of colour
        datap = ptr32(self.data)
        #datap = data
        for z in range(4):
            zb = 0x10 >> z
            #zz = z * 96
            if (c & zb):
                datap[byteoff] |= bit
            else:
                datap[byteoff] &= nbit
            byteoff += h
            zb = 0x400 >> z
            if (c & zb):
                datap[byteoff] |= bit
            else:
                datap[byteoff] &= nbit
            byteoff += h
            zb = 0x8000 >> z
            if (c & zb):
                datap[byteoff] |= bit
            else:
                datap[byteoff] &= nbit
            byteoff += (24*4*h)-(2*h)#94 # 96-2

    @micropython.viper
    #@micropython.native
    def setpixel(self, x : int,y : int,r : int,g : int,b : int):
        if x < 0 or x > 63:
            return
        h = int(self.HEIGHT)
        if y < 0 or y > 16*h:
            return
        bitoff = (((x&7) << 1) + ((y & 4) << 2)) * h + ((y & 8) >> 3)
        bitoff += (y>>4) << 1
        byteoff = (((y&3) * 24) + (((x & 0x38) >> 3) * 3 )) * h
        
        bitoff += byteoff << 5
        
        byteoff = bitoff >> 5
        bitoff = bitoff & 0x1f
        
        bit = 1 << bitoff
        nbit = (-1) ^ bit
        
        # bit of colour
        datap = ptr32(self.data)
        #datap = data
        for z in range(4):
            zb = 0x80 >> z
            #zz = z * 96
            if (b & zb):
                datap[byteoff] |= bit
            else:
                datap[byteoff] &= nbit
            byteoff += h
            if (g & zb):
                datap[byteoff] |= bit
            else:
                datap[byteoff] &= nbit
            byteoff += h
            if (r & zb):
                datap[byteoff] |= bit
            else:
                datap[byteoff] &= nbit
            byteoff += (24*4*h)-(2*h)#94 # 96-2

    def setconfig(self, v):
        self.clk.value(0)
        self.le.value(0)
        for x in range(24):
            for b in range(16):
                if x==23 and b == 12:
                    self.le.value(1)
                d = 1 if ((0x8000 >> b) & v ) != 0  else 0
                for dp in self.data_pins:
                    self.data_pins[dp].value(d)
#                self.d1.value( d )
#                self.d2.value( d )
                self.clk.value(1)
                self.clk.value(0)
        self.le.value(0)

    # 0-255
    def SetBrightness(self,b):
        self.setconfig( 0x7140 | ((b>>2) & 0x3f))

    @micropython.viper
    def DoFB(self,f):
        pp = f.pixel
        sp = self.setpixel2
        c = 0
        for y in range(16):
            for x in range(64):
                c = int(pp(x,y))
                sp(x,y,c)

    def _initDMA(self, ch0, ch1):
        d = DmaChannel(ch0)
        d.SetReadAddress(0) # init-ed by ch1
        d.SetIncRead(True)
        d.SetWriteAddress( 0x50200000 + 0x10 ) # PIO0_BASE + TXF0
        d.SetIncWrite(False)
        d.SetTransferCount(24*4*4*self.HEIGHT)
        d.SetTransferSize(2) # dword
        d.SetTransferSignal(0) # DREQ_PIO0_TX0
        d.SetChainChannel(ch1)
        d.WriteControlValue() # not trigger

        d1 = DmaChannel(ch1)
        d1.SetReadAddress(self.data_addr2)
        d1.SetIncRead(False)
        d1.SetWriteAddress( d.addr + 0x3c ) # AL3_READ_ADDR_TRIG
        d1.SetIncWrite(False)
        d1.SetTransferCount(1)
        d1.SetTransferSize(2) # dword
        
        self._dma0 = d
        self._dma1 = d1
    
    @micropython.viper
    def _getaddr(x) -> int:
        return int(ptr32(x))
    
    
    def runDMA(self):
        data_addr = LedPanel._getaddr(self.data) #uctypes.addressof(data)
        self.data_addr_buf = struct.pack("I",data_addr)
        self.data_addr2 = LedPanel._getaddr(self.data_addr_buf) # uctypes.addressof(data_addr_buf)

        self._initDMA(0,1)
        self._dma1.Trigger()

    def stopDMA(self):
        self._dma1.SetEnable(False)
        self._dma1.WriteControlValue()


if __name__ == "__main__":
    print("ok")
    x = LedPanel()
    for z in range(32):
        x.setpixel(z,z,255,0,0)
    x.setpixel(0,0,255,0,0)
    x.setpixel(1,1,0,255,0)
    x.setpixel(2,2,0,0,255)
#    x.data[0]=1 | 4
 #   x.data[48]=1<<4
    x.start()
    for y in range(500):
        x.putData()
    x.end()
    print("done")
    x.oe.value(1)
