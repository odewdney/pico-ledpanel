
class DmaChannel:
    DMA_BASE = 0x50000000
    
    # registers
    READ_ADDR = 0
    WRITE_ADDR = 1
    TRANS_COUNT = 2
    CTRL_TRIG = 3
    AL1_CTRL = 4
    # c r w t
    # c t r w
    # c w w r
    AL3_READ_ADDR_TRIG = 15

    DREQ_PIO0_TX0 = 0
    DREQ_SPI0_TX = 16
    DREQ_UART0_TX = 20
    DREQ_PWM_WRAP0 = 24
    DREQ_I2C_TX = 32
    DREQ_ADC = 36
    DREQ_TIMER1 = 0x3b
    DREQ_UNPACED = 0x3f

    """DMA Wrapper"""
    def __init__(self,channelNum):
        self.addr = DmaChannel.DMA_BASE + 0x40 * channelNum
        self.ControlValue = 0x3F8033 # q,t(31),incW,IncR,byte,hiPri,en
        self.SetChainChannel(channelNum) #so that the chain value is set to itself
    
    @micropython.viper
    def SetReadAddress(self, address: uint):
        ptr= ptr32(self.addr)
        ptr[0] = address
    @micropython.viper
    def SetReadAddressTrigger(self, address: uint):
        ptr= ptr32(self.addr)
        ptr[15] = address
    @micropython.viper
    def SetWriteAddress(self, address: uint):
        ptr= ptr32(self.addr)
        ptr[1] = address
    @micropython.viper
    def SetTransferCount(self, count: uint):
        ptr= ptr32(self.addr)
        ptr[2] = count
    @micropython.viper
    def WriteControlValue(self):
        ptr= ptr32(self.addr)
        ptr[4] = int(self.ControlValue)
    def SetControlValue(self, mask, value):
        self.ControlValue = (self.ControlValue & ~mask) | value
    def SetTransferSignal(self, ch:uint):
        self.SetControlValue(0x1f8000, ch << 15)
    def SetChainChannel(self, ch:uint):
        self.SetControlValue(0x7800, ch << 11)
    # ring_sel 1
    # ring_size 4
    def SetIncWrite(self, inc:bool):
        self.SetControlValue(0x20, 0x20 if inc else 0)
    def SetIncRead(self, inc:bool):
        self.SetControlValue(0x10, 0x10 if inc else 0)
    def SetTransferSize(self, sz:uint):
        self.SetControlValue(0xc, sz << 2)
    # prio
    def SetEnable(self, inc:bool):
        self.SetControlValue(0x1, 0x1 if inc else 0)

    @micropython.viper
    def Trigger(self):
        ptr= ptr32(self.addr)
        ptr[3] = int(self.ControlValue)
        
    @micropython.viper
    def ReadReadAddress(self) -> int:
        ptr= ptr32(self.addr)
        return ptr[0]
    @micropython.viper
    def ReadWriteAddress(self) -> int:
        ptr= ptr32(self.addr)
        return ptr[1]
    @micropython.viper
    def ReadTransferCount(self) -> int:
        ptr= ptr32(self.addr)
        return ptr[2]
    @micropython.viper
    def ReadControlValue(self) -> int:
        ptr= ptr32(self.addr)
        return ptr[3]
        
    def isBusy(self):
        return (self.ReadControlValue() & 0x01000000 ) != 0

if __name__ == "__main__":
    print("ok")