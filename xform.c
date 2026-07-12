/* xform — Custom stream cipher transformation utility.
 *
 * Reads all of stdin, applies a proprietary stream cipher, writes to stdout.
 * Original source is lost. This is a reimplementation for task generation.
 *
 * Algorithm: 128-bit state stream cipher with non-linear mixing round.
 * Processing: 4-byte chunks, state-dependent tail handling.
 * Not any published PRNG — custom shift triples, extra additive constant.
 *
 * Build: gcc -O2 -s -o xform xform.c
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* --- State and key derivation --- */

static uint32_t s[4];  /* 128-bit internal state */

/* Derive initial state from two 64-bit hardcoded constants.
 * The actual key bytes never appear literally in the binary — they're the
 * output of this mixing function, which must be traced to understand. */
static void init_state(void) {
    uint64_t k0 = 0x9E3779B97F4A7C15ULL;  /* golden ratio + SplitMix64 gamma */
    uint64_t k1 = 0xBB67AE8584CAA73BULL;  /* another well-known constant */

    /* Mix the two seed values into four 32-bit state words */
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

/* --- Non-linear mixing round ---
 *
 * Advances state and returns the 32-bit output word.
 *
 * This looks like xorshift128 in disassembly (three shifts + XORs on four
 * 32-bit registers) but uses CUSTOM shift amounts (9, 14, 6) that are NOT
 * any published variant. Standard xorshift128 uses (11, 8, 19).
 * Additionally, an additive step (+0x9E3779B9) breaks pure-xor linearity.
 */
static uint32_t step(void) {
    uint32_t t, w;

    t  = s[0];
    t ^= t << 9;        /* custom — not the standard 11 */
    t ^= t >> 14;       /* custom — not the standard 8 */
    s[0] = s[1];
    s[1] = s[2];
    s[2] = s[3];
    w   = s[3];
    w  ^= w >> 6;       /* custom — not the standard 19 */
    w  ^= t;
    w  += 0x9E3779B9;   /* extra additive constant — breaks pure XOR pattern */
    s[3] = w;
    return w;
}

/* --- Main transformation --- */

int main(void) {
    unsigned char *input, *output;
    size_t len, cap, out_len;
    size_t pos = 0, out_pos = 0;

    cap = 4096;
    input = (unsigned char *)malloc(cap);
    len = 0;
    /* Read all of stdin */
    {
        size_t n;
        while ((n = fread(input + len, 1, cap - len, stdin)) > 0) {
            len += n;
            if (len == cap) {
                cap *= 2;
                input = (unsigned char *)realloc(input, cap);
            }
        }
    }

    out_len = len;  /* output same length as input */
    output = (unsigned char *)malloc(out_len ? out_len : 1);

    init_state();

    /* Process full 4-byte chunks: one step() produces 4 keystream bytes */
    while (pos + 4 <= len) {
        uint32_t w = step();
        output[out_pos++] = input[pos++] ^ ((w >> 0)  & 0xFF);
        output[out_pos++] = input[pos++] ^ ((w >> 8)  & 0xFF);
        output[out_pos++] = input[pos++] ^ ((w >> 16) & 0xFF);
        output[out_pos++] = input[pos++] ^ ((w >> 24) & 0xFF);
    }

    /* Tail handling: 0-3 leftover bytes.
     * One step() produces 4 keystream bytes. Only the first r are used.
     * CRITICAL: state still advances by one step. Keystream bytes 4-r..3
     * are consumed/discarded. This is NOT zero-padding — the keystream
     * schedule depends on input length mod 4. */
    if (pos < len) {
        uint32_t w = step();
        while (pos < len) {
            output[out_pos++] = input[pos++] ^ (w & 0xFF);
            w >>= 8;
        }
    }

    if (out_len > 0) {
        fwrite(output, 1, out_len, stdout);
    }

    free(input);
    free(output);
    return 0;
}
