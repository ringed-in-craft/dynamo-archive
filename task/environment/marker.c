#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "Usage: marker <file>\n");
        return 1;
    }

    FILE *f = fopen(argv[1], "rb");
    if (!f) {
        perror("fopen");
        return 1;
    }

    uint32_t a = 0x9E3779B9;
    uint32_t b = 0x7F4A7C15;

    int byte;
    while ((byte = fgetc(f)) != EOF) {
        a = (a + (uint8_t)byte) & 0xFFFFFFFF;
        a = (a ^ (a >> 13)) & 0xFFFFFFFF;
        a = (a * 0x41C64E6D + 0x6073) & 0xFFFFFFFF;
        b = (b ^ (uint8_t)byte) & 0xFFFFFFFF;
        b = ((b << 7) | (b >> 25)) & 0xFFFFFFFF;
        b = (b + a) & 0xFFFFFFFF;
    }

    fclose(f);

    uint32_t result = (a ^ b ^ 0xA5A5A5A5) & 0xFFFFFFFF;
    printf("%08X\n", result);
    return 0;
}
