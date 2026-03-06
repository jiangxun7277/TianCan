#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <windows.h>
#include <intrin.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

int check_cpu_timing() {
    unsigned __int64 t1, t2;
    t1 = __rdtsc();
    volatile int a = 0;
    for (int i = 0; i < 1000; i++) a += i;
    t2 = __rdtsc();
    if ((t2 - t1) > 5000000) return 0;
    return 1;
}

void rc4_crypt(unsigned char* data, int data_len, unsigned char* key, int key_len) {
    int S[256], i, j = 0, k;
    unsigned char temp;
    for (i = 0; i < 256; i++) S[i] = i;
    for (i = 0; i < 256; i++) {
        j = (j + S[i] + key[i % key_len]) % 256;
        temp = S[i]; S[i] = S[j]; S[j] = temp;
    }
    i = 0; j = 0;
    for (k = 0; k < data_len; k++) {
        i = (i + 1) % 256;
        j = (j + S[i]) % 256;
        temp = S[i]; S[i] = S[j]; S[j] = temp;
        data[k] ^= S[(S[i] + S[j]) % 256];
    }
}

void burn_memory(void* ptr, size_t size) {
    volatile unsigned char* p = (volatile unsigned char*)ptr;
    while (size--) *p++ = 0;
}

enum OpCodeInternal {
    OP_NI_HE = 0, OP_JU_ZHEN, OP_XUAN_RAN, OP_YING_SHE,
    OP_XIAN_XIAO, OP_XUN_LU, OP_GUI_YI, OP_COUNT
};

int instruction_map[256];
unsigned long long rng_state = 0;

void seed_rng(int seed) { rng_state = (unsigned long long)seed; }
int next_rand(int max) {
    rng_state = (rng_state * 6364136223846793005ULL + 1);
    return (int)((rng_state >> 33) % max);
}

void init_vm_map(int session_seed) {
    int pool[256];
    int i, j, temp;
    seed_rng(session_seed);
    for(i=0; i<256; i++) instruction_map[i] = -1;
    for(i=0; i<256; i++) pool[i] = i;
    for (i = 255; i > 0; i--) {
        j = next_rand(i + 1);
        temp = pool[i]; pool[i] = pool[j]; pool[j] = temp;
    }
    for (i = 0; i < OP_COUNT; i++) {
        instruction_map[pool[i]] = i;
    }
}

typedef struct {
    int R[4];
    int pc;
    unsigned int junk_flag;
} VirtualCPU;

int run_vm(const unsigned char* bytecode, int bytecode_len) {
    VirtualCPU cpu;
    unsigned char raw_op;
    int internal_op;
    int reg1, reg2, val;
    int probe_args[2] = {10, 20};

    cpu.R[0] = 0; cpu.R[1] = 0; cpu.R[2] = 0; cpu.R[3] = 0;
    cpu.pc = 0;
    cpu.junk_flag = 0xDEAD;

    while (cpu.pc < bytecode_len) {
        raw_op = bytecode[cpu.pc++];
        internal_op = instruction_map[raw_op];

        switch (internal_op) {
            case OP_NI_HE:
                reg1 = bytecode[cpu.pc++];
                val = bytecode[cpu.pc++];
                cpu.R[reg1] = val;
                break;
            case OP_JU_ZHEN:
                reg1 = bytecode[cpu.pc++];
                val = bytecode[cpu.pc++];
                cpu.R[reg1] = probe_args[val];
                break;
            case OP_XUAN_RAN:
                reg1 = bytecode[cpu.pc++];
                reg2 = bytecode[cpu.pc++];
                cpu.R[reg1] = cpu.R[reg1] + cpu.R[reg2];
                break;
            case OP_YING_SHE:
                reg1 = bytecode[cpu.pc++];
                reg2 = bytecode[cpu.pc++];
                cpu.R[reg1] = cpu.R[reg1] * cpu.R[reg2];
                break;
            case OP_XIAN_XIAO:
                cpu.junk_flag ^= cpu.R[0];
                cpu.junk_flag = (cpu.junk_flag << 2) | 0x1337;
                break;
            case OP_XUN_LU:
                cpu.junk_flag += cpu.R[1] * 99;
                break;
            case OP_GUI_YI:
                reg1 = bytecode[cpu.pc++];
                return cpu.R[reg1];
            default:
                return 0;
        }
    }
    return 0;
}

static PyObject* tiancan_execute(PyObject* self, PyObject* args) {
    int seed;
    const unsigned char* bytecode;
    Py_ssize_t bytecode_len;
    const char* encrypted_data;
    Py_ssize_t data_len;
    const char* salt;
    Py_ssize_t salt_len;

    if (!PyArg_ParseTuple(args, "iy#y#s#", &seed, &bytecode, &bytecode_len, &encrypted_data, &data_len, &salt, &salt_len)) {
        return NULL;
    }

    init_vm_map(seed);

    int vm_result = run_vm(bytecode, (int)bytecode_len);

    if (check_cpu_timing() == 0) vm_result += 111;

    char key_buffer[128];
    snprintf(key_buffer, sizeof(key_buffer), "%d%s", vm_result, salt);

    unsigned char* buffer = (unsigned char*)malloc(data_len + 1);
    if (!buffer) return PyErr_NoMemory();
    memcpy(buffer, encrypted_data, data_len);
    buffer[data_len] = '\0';

    rc4_crypt(buffer, (int)data_len, (unsigned char*)key_buffer, (int)strlen(key_buffer));

    int ret = PyRun_SimpleString((char*)buffer);

    burn_memory(buffer, data_len);
    free(buffer);

    if (ret != 0) {
        PyErr_SetString(PyExc_RuntimeError, "System Integrity Violation.");
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyMethodDef TianCanMethods[] = {
    {"run_secure", tiancan_execute, METH_VARARGS, "Execute."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef tiancanmodule = {
    PyModuleDef_HEAD_INIT, "security", "TianCan V1.0 Core", -1, TianCanMethods
};

PyMODINIT_FUNC PyInit_security(void) {
    return PyModule_Create(&tiancanmodule);
}