/* xform — Custom stream cipher transformation utility.
 *
 * Reads all of stdin, applies a proprietary stream cipher, writes to stdout.
 * The cipher is INPUT-DEPENDENT: each input word feeds back into the state,
 * so the keystream cannot be precomputed from null bytes.
 *
 * Build: gcc -O2 -s -o xform xform.c
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
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

static uint32_t step(uint32_t input_word) {
    uint32_t t, w, result;
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
    result = w;               /* save pre-feedback value for output */
    w  ^= input_word;         /* mix input into state (not output) */
    s[3] = w;
    return result;
}

int main(void) {
    unsigned char *input, *output;
    size_t len = 0, cap = 4096;
    size_t pos = 0, out_pos = 0;

    input = (unsigned char *)malloc(cap);
    {
        size_t n;
        while ((n = fread(input + len, 1, cap - len, stdin)) > 0) {
            len += n;
            if (len == cap) { cap *= 2; input = (unsigned char *)realloc(input, cap); }
        }
    }

    output = (unsigned char *)malloc(len ? len : 1);
    init_state();

    /* Process full 4-byte chunks */
    while (pos + 4 <= len) {
        uint32_t word = (uint32_t)input[pos]
                      | ((uint32_t)input[pos+1] << 8)
                      | ((uint32_t)input[pos+2] << 16)
                      | ((uint32_t)input[pos+3] << 24);
        uint32_t w = step(word);
        output[out_pos++] = input[pos++] ^ ((w >> 0)  & 0xFF);
        output[out_pos++] = input[pos++] ^ ((w >> 8)  & 0xFF);
        output[out_pos++] = input[pos++] ^ ((w >> 16) & 0xFF);
        output[out_pos++] = input[pos++] ^ ((w >> 24) & 0xFF);
    }

    /* Tail: pad to 4 bytes with zeros, feed as word, use first r output bytes */
    if (pos < len) {
        uint32_t word = 0;
        int r = 0;
        while (pos < len) {
            word |= ((uint32_t)input[pos++]) << (r * 8);
            r++;
        }
        uint32_t w = step(word);
        pos -= r;  /* reset for output loop */
        while (pos < len) {
            output[out_pos++] = input[pos++] ^ (w & 0xFF);
            w >>= 8;
        }
    }

    if (len > 0) fwrite(output, 1, len, stdout);
    free(input);
    free(output);
    return 0;
}
