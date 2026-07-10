/* slogdec.c — Correct .slog decoder. Compile: gcc -s -O2 -o slogdec slogdec.c */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

#define BLOCK_SIZE 256
#define MAGIC "SLOG"

typedef struct {
    uint32_t base_ts;
    uint8_t  offset;
    uint8_t  sensor_id;
    float    value;
    char     _pad[6]; /* record is 6 bytes: offset(1) + sensor_id(1) + value(4) */
} __attribute__((packed)) record_t;

typedef struct {
    uint32_t base_ts;
    record_t records[BLOCK_SIZE];
} __attribute__((packed)) block_t;

int main(int argc, char **argv) {
    const char *path = "/app/data/sample.slog";
    if (argc > 1) path = argv[1];

    FILE *f = fopen(path, "rb");
    if (!f) { fprintf(stderr, "Cannot open %s\n", path); return 1; }

    char magic[5] = {0};
    fread(magic, 1, 4, f);
    if (strcmp(magic, MAGIC) != 0) { fprintf(stderr, "Bad magic\n"); return 1; }

    uint16_t bs;
    fread(&bs, 2, 1, f);
    (void)bs;

    printf("[\n");
    int first = 1;

    while (1) {
        uint32_t base;
        if (fread(&base, 4, 1, f) != 1) break;

        for (int i = 0; i < BLOCK_SIZE; i++) {
            uint8_t buf[6];
            if (fread(buf, 6, 1, f) != 1) break;

            uint8_t off    = buf[0];
            uint8_t sid    = buf[1];
            uint32_t ts    = base + off;
            float val;
            memcpy(&val, buf + 2, 4);

            if (!first) printf(",\n");
            first = 0;
            printf("  {\"timestamp\": %u, \"sensor_id\": %u, \"value\": %.6f}", ts, sid, val);
        }
    }

    printf("\n]\n");
    fclose(f);
    return 0;
}
