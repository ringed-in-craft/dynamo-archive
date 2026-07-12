/* Test harness to dump state transitions */
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static uint32_t s[4];

static void init_state(void) {
    uint64_t k0 = 0x9E3779B97F4A7C15ULL;
    uint64_t k1 = 0xBB67AE8584CAA73BULL;
    k0 ^= (k0 >> 33);
    k0 *= 0xFF51AFD7ED558CCDULL;
    k0 ^= (k0 >> 33);
    k1 ^= (k1 >> 33);
    k1 *= 0xC4CEB9FE1A85EC53ULL;
    k1 ^= (k1 >> 33);
    s[0] = (uint32_t)(k0 & 0xFFFFFFFF);
    s[1] = (uint32_t)((k0 >> 32) & 0xFFFFFFFF);
    s[2] = (uint32_t)(k1 & 0xFFFFFFFF);
    s[3] = (uint32_t)((k1 >> 32) & 0xFFFFFFFF);
}

static uint32_t step(void) {
    uint32_t t, w;
    t  = s[0];
    t ^= t << 9;
    t ^= t >> 14;
    s[0] = s[1];
    s[1] = s[2];
    s[2] = s[3];
    w   = s[3];
    w  ^= w >> 6;
    w  ^= t;
    w  += 0x9E3779B9;
    s[3] = w;
    return w;
}

int main(void) {
    init_state();
    printf("init: %08x %08x %08x %08x\n", s[0], s[1], s[2], s[3]);

    unsigned char input[] = "The quick brown fox jumps over the lazy dog.";
    int len = strlen((char*)input);
    printf("len=%d\n", len);

    unsigned char *output = (unsigned char*)malloc(len);
    int pos = 0, out_pos = 0;

    while (pos + 4 <= len) {
        uint32_t w = step();
        printf("step: w=%08x\n", w);
        output[out_pos++] = input[pos++] ^ ((w >> 0)  & 0xFF);
        output[out_pos++] = input[pos++] ^ ((w >> 8)  & 0xFF);
        output[out_pos++] = input[pos++] ^ ((w >> 16) & 0xFF);
        output[out_pos++] = input[pos++] ^ ((w >> 24) & 0xFF);
    }

    if (pos < len) {
        uint32_t w = step();
        printf("tail: w=%08x\n", w);
        while (pos < len) {
            output[out_pos++] = input[pos++] ^ (w & 0xFF);
            w >>= 8;
        }
    }

    printf("output: ");
    for (int i = 0; i < len; i++) printf("%02x", output[i]);
    printf("\n");
    return 0;
}
