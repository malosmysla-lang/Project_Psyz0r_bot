/* Linux regression: exercise the actual minqlx hook allocator over 100 VM reloads.
   Instruction decoding is stubbed; allocation, patching and rewind are real. */
#include <assert.h>
#include <string.h>
#include "simple_hook.c"
BOOL CreateTrampolineFunction(PTRAMPOLINE ct) {
    ct->nIP=1; ct->oldIPs[0]=14; return TRUE;
}
static void replacement(void) {}
int main(void) {
    void *page=mmap(NULL,4096,PROT_READ|PROT_WRITE|PROT_EXEC,MAP_ANONYMOUS|MAP_PRIVATE,-1,0);
    assert(page!=MAP_FAILED); void *original;
    for(int i=0;i<10;i++)assert(Hook(page,replacement,&original)==0);
    int previous_custom=0;
    for(int vm=0;vm<100;vm++) {
        if(previous_custom)assert(seek_hook_slot(-previous_custom));
        previous_custom=0;
        for(int i=0;i<4;i++){assert(Hook(page,replacement,&original)==0);previous_custom++;}
        for(int i=0;i<3;i++)assert(Hook(page,replacement,&original)==0);
        assert(seek_hook_slot(-3));
        assert(last_trmp==14);
    }
    munmap(page,4096);puts("100 VM reloads: permanent and custom hook slots preserved");
    return 0;
}
