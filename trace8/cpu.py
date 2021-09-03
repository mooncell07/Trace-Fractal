from collections import deque

import pygame

from .utils import FONTS, Logger

__all__ = ("CPU",)
pygame.init()


class CPU:

    __slots__ = (
        "_log",
        "_memory",
        "_display_buffer",
        "_logflag",
        "V",
        "pc",
        "I",
        "st",
        "dt",
        "stack",
        "opcode",
        "keymap",
        "draw_flag",
    )

    def __init__(self, *, log: bool = True) -> None:

        self.keymap = [0] * 16  # 16 availabel keys

        self.arm_registers()
        self.arm_memory_units()
        self.arm_keyboard()
        self.load_fonts()

        self.opcode: int = 0
        self.draw_flag = False

        self._log = Logger(__name__)
        self._logflag = log

    @property
    def _vx(self):
        """
        x-pos register.
        """
        return (self.opcode & 0x0F00) >> 8

    @property
    def _vy(self):
        """
        y-pos register.
        """
        return (self.opcode & 0x00F0) >> 4

    @property
    def _kk(self):
        """
        wtf is this for.
        """
        return self.opcode & 0x00FF

    @property
    def _nn(self):
        """
        probably max height.
        """
        return self.opcode & 0x000F

    def arm_memory_units(self) -> None:
        """
        Initializes memory and Regen Buffer
        """
        # 4 KBs of RAM as per standard limit for CHIP8 module.
        # Using 0 to represent an empty mem loc.
        self._memory = [0] * 4096

        # Display Buffer/Memory as per standard limit for CHIP8.
        # For storing the pixel state on the display.
        self._display_buffer = [0] * 64 * 32

    def arm_registers(self):
        """
        Initializes registers.
        """
        self.V = [0] * 16  # 16 general purpose registers.
        self.pc = 0x200  # program counter starting at 0x200'th (or 512'th) mem loc.

        # Index counter for storing memory addresses.
        self.I = 0  # noqa E741

        # CPU interupts.
        self.st = 0
        self.dt = 0

        # A stack for storing program counter states.
        self.stack: deque = deque()

    def arm_keyboard(self):
        """
        Initializes keyboard.
        """
        k_inps = pygame.key.get_pressed()

        self.keymap[0] = k_inps[pygame.K_1]
        self.keymap[1] = k_inps[pygame.K_2]
        self.keymap[2] = k_inps[pygame.K_3]
        self.keymap[3] = k_inps[pygame.K_4]
        self.keymap[4] = k_inps[pygame.K_q]
        self.keymap[5] = k_inps[pygame.K_w]
        self.keymap[6] = k_inps[pygame.K_e]
        self.keymap[7] = k_inps[pygame.K_r]
        self.keymap[8] = k_inps[pygame.K_a]
        self.keymap[9] = k_inps[pygame.K_s]
        self.keymap[10] = k_inps[pygame.K_d]
        self.keymap[11] = k_inps[pygame.K_f]
        self.keymap[12] = k_inps[pygame.K_z]
        self.keymap[13] = k_inps[pygame.K_x]
        self.keymap[14] = k_inps[pygame.K_c]
        self.keymap[15] = k_inps[pygame.K_v]

    def load_fonts(self) -> None:
        """
        Loads fonts in the memory.
        """
        for i, item in enumerate(FONTS):
            self._memory[i] = item

    def load_rom(self, path: str) -> None:
        """
        loads ROM in memory.
        """
        with open(path, "rb") as rom:
            for i, bnry in enumerate(rom.read()):
                self._memory[
                    i + self.pc
                ] = bnry  # loading ROM in locations after fontset.

    def debugworks(self) -> None:
        """
        Writes debug log.
        """
        lgr = self._log.create_logger()
        lgr.debug(self._log.generate_log(self))

    def fetch_op(self):
        """
        Fetches the current opcode.
        """
        opcode = (self._memory[self.pc] << 8) | (self._memory[self.pc + 1])
        self.opcode = opcode

    def op_CLS(self):
        """
        0x00E0 - Cleans the screen
        """
        ...

    def op_LD_Vx_byte(self):
        """
        0x6000 - Loads kk on the registers.
        """
        self.V[self._vx] = self._kk

    def op_LD_I_ADDR(self):
        """
        0xa000 - Loads index register.
        """
        self.I = self.opcode & 0x0FFF  # noqa E741

    def op_DRW_Vx_Vy_nibble(self):
        """
        0xd000 - Draws Vx and Vn on screen.
        """
        self.V[0xF] = 0  # Resetting register

        # x and y coordinates for pixel
        x = self.V[self._vx] & 0xFF
        y = self.V[self._vy] & 0xFF

        height = self._nn
        row = 0

        while height > row:
            pixel = self._memory[self.I + row]

            for pxo in range(8):

                if 8 > pxo:
                    if (pixel & (0x80 >> pxo)) != 0:

                        if self._display_buffer[(x + pxo + ((y + row) * 64))] == 1:
                            self.V[0xF] = 1

                        self._display_buffer[x + pxo + ((y + row) * 64)] ^= 1
            row += 1

        self.draw_flag = True
        self.pc += 2

    def op_CALL_ADDR(self):
        """
        Call subroutine at nnn.
        """
        self.stack.append(self.pc)
        self.pc = self.opcode & 0x0FFF

    @property
    def _opmap(self):
        """
        property for storing subroutines.
        """
        opmap = {
            0x00E0: self.op_CLS,
            0x6000: self.op_LD_Vx_byte,
            0xA000: self.op_LD_I_ADDR,
            0xD000: self.op_DRW_Vx_Vy_nibble,
            0x2000: self.op_CALL_ADDR,
        }
        return opmap

    def cycle(self):
        """
        The main execution cycle of cpu.
        """
        self.fetch_op()
        exop = self.opcode & 0xF000
        self._opmap[exop]()
        self.pc += 2
        if self._logflag:
            self.debugworks()
