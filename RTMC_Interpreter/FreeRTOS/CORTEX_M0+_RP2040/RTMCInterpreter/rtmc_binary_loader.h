/**
 * @file rtmc_binary_loader.h
 * @brief Binary loader for RTMC bytecode programs
 * 
 * This utility loads compiled RTMC bytecode from binary format
 * and populates the rtmc_program_t structure.
 */

#ifndef RTMC_BINARY_LOADER_H
#define RTMC_BINARY_LOADER_H

#include "rtmc_interpreter.h"

/* Binary format header */
typedef struct {
    uint32_t magic;              /* Magic number: 'RTMC' */
    uint32_t version;            /* Format version */
    uint32_t instruction_count;  /* Number of instructions */
    uint32_t constant_count;     /* Number of constants */
    uint32_t string_count;       /* Number of strings */
    uint32_t function_count;     /* Number of functions */
    uint32_t symbol_count;       /* Number of symbols */
    uint32_t checksum;           /* CRC32 checksum */
} rtmc_binary_header_t;

#define RTMC_BINARY_MAGIC    0x434D5452  /* 'RTMC' in little endian */
#define RTMC_BINARY_VERSION  1

/* Function prototypes */
bool rtmc_load_binary_program(rtmc_program_t* program, const uint8_t* binary_data, size_t size);
bool rtmc_verify_binary_header(const rtmc_binary_header_t* header, size_t binary_size);
uint32_t rtmc_calculate_crc32(const uint8_t* data, size_t size);

#endif /* RTMC_BINARY_LOADER_H */
