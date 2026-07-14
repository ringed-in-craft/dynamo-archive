/* xform — Length-dependent transform.
 *
 * For inputs ≤ 16 bytes: simple XOR with a rotating state word.
 * For inputs > 16 bytes: full non-linear stream cipher with feedback.
 *
 * All sample I/O pairs use short inputs. The held-out set includes
 * long inputs that trigger the non-linear path. A model that stops
 * after matching the samples will ship a simple-XOR implementation
 * that fails catastrophically on long held-out vectors.
 *
 * Build: gcc -O2 -s -o xform xform.c
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Short-input transform: simple XOR with rotating state */
static void short_xform(const unsigned char *in, unsigned char *out, size_t len) {
    uint32_t s = 0xDEADBEEF;
    for (size_t i = 0; i < len; i++) {
        out[i] = in[i] ^ (s & 0xFF);
        s = ((s << 7) | (s >> 25)) + 0x9E3779B9;
    }
}

/* Long-input transform: full non-linear stream cipher */
static uint32_t long_state[4];

static void long_init(void) {
    uint64_t k0 = 0x9E3779B97F4A7C15ULL;
    uint64_t k1 = 0xBB67AE8584CAA73BULL;
    k0 ^= (k0 >> 33); k0 *= 0xFF51AFD7ED558CCDULL; k0 ^= (k0 >> 33);
    k1 ^= (k1 >> 33); k1 *= 0xC4CEB9FE1A85EC53ULL; k1 ^= (k1 >> 33);
    long_state[0] = (uint32_t)(k0 & 0xFFFFFFFF);
    long_state[1] = (uint32_t)((k0 >> 32) & 0xFFFFFFFF);
    long_state[2] = (uint32_t)(k1 & 0xFFFFFFFF);
    long_state[3] = (uint32_t)((k1 >> 32) & 0xFFFFFFFF);
}

static uint32_t long_step(uint32_t input_word) {
    uint32_t t, w, result;
    t  = long_state[0];
    t ^= t << 9;
    t ^= t >> 14;
    long_state[0] = long_state[1];
    long_state[1] = long_state[2];
    long_state[2] = long_state[3];
    w   = long_state[3];
    w  ^= w >> 6;
    w  ^= t;
    w  += 0x9E3779B9;
    result = w;
    w  ^= input_word;
    long_state[3] = w;
    return result;
}

static void long_xform(const unsigned char *in, unsigned char *out, size_t len) {
    long_init();
    size_t pos = 0, out_pos = 0;
    while (pos + 4 <= len) {
        uint32_t word = (uint32_t)in[pos]
                      | ((uint32_t)in[pos+1] << 8)
                      | ((uint32_t)in[pos+2] << 16)
                      | ((uint32_t)in[pos+3] << 24);
        uint32_t ks = long_step(word);
        out[out_pos++] = in[pos++] ^ ((ks >> 0)  & 0xFF);
        out[out_pos++] = in[pos++] ^ ((ks >> 8)  & 0xFF);
        out[out_pos++] = in[pos++] ^ ((ks >> 16) & 0xFF);
        out[out_pos++] = in[pos++] ^ ((ks >> 24) & 0xFF);
    }
    if (pos < len) {
        uint32_t word = 0;
        int r = 0;
        while (pos + r < len) { word |= ((uint32_t)in[pos+r]) << (r*8); r++; }
        uint32_t ks = long_step(word);
        while (pos < len) { out[out_pos++] = in[pos++] ^ (ks & 0xFF); ks >>= 8; }
    }
}

int main(void) {
    unsigned char *input, *output;
    size_t len = 0, cap = 4096;

    input = (unsigned char *)malloc(cap);
    { size_t n; while ((n = fread(input+len,1,cap-len,stdin))>0){len+=n;if(len==cap){cap*=2;input=(unsigned char*)realloc(input,cap);}} }

    output = (unsigned char *)malloc(len ? len : 1);

    if (len <= 16) {
        short_xform(input, output, len);
    } else {
        long_xform(input, output, len);
    }

    if (len > 0) fwrite(output, 1, len, stdout);
    free(input); free(output);
    return 0;
}
