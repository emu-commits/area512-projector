// An AREA512 Ruby app's .mrb files, run on the PC on mruby/c with the firmware's settings and
// an arena of a given size, the way the sandbox runs main.manifest: each file's bytes kept in
// the arena, loaded and run in one VM. Files are on the host (not in the arena, as on the
// card); keys come from a file. Exit 0 when the keys run out, 3 when the arena does.
// tests/arena.sh builds it and runs it.
//
//   arena <arena bytes> <root dir> <keys file> <file.mrb>...
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <sys/stat.h>
#include <unistd.h>
#include "mrubyc.h"

static uint8_t *pool;
static const char *root;
static char **keys; static int n_keys, at_key;
static int min_free = 1 << 30;

void arena_oom(void) { printf("@@OOM key=%d\n", at_key); fflush(stdout); exit(3); }

static void host_path(char *out, mrbc_value *v) {
  snprintf(out, 1024, "%s%.*s", root, mrbc_string_size(v), mrbc_string_cstr(v));
}
static void c_read(mrbc_vm *vm, mrbc_value v[], int argc) {
  char p[1024]; host_path(p, &v[1]);
  FILE *f = fopen(p, "rb"); if (!f) { SET_NIL_RETURN(); return; }
  fseek(f, 0, SEEK_END); long n = ftell(f); fseek(f, 0, SEEK_SET);
  char *b = malloc(n + 1); fread(b, 1, n, f); fclose(f);
  mrbc_value s = mrbc_string_new(vm, b, n); free(b);
  SET_RETURN(s);
}
static void c_write(mrbc_vm *vm, mrbc_value v[], int argc) {
  char p[1024]; host_path(p, &v[1]);
  FILE *f = fopen(p, "wb"); fwrite(mrbc_string_cstr(&v[2]), 1, mrbc_string_size(&v[2]), f); fclose(f);
  SET_INT_RETURN(mrbc_string_size(&v[2]));
}
static void c_kind(mrbc_vm *vm, mrbc_value v[], int argc) {
  char p[1024]; host_path(p, &v[1]); struct stat st;
  SET_INT_RETURN(stat(p, &st) != 0 ? 0 : S_ISDIR(st.st_mode) ? 2 : 1);
}
static void c_mkdir(mrbc_vm *vm, mrbc_value v[], int argc) { char p[1024]; host_path(p, &v[1]); mkdir(p, 0755); SET_NIL_RETURN(); }
static void c_unlink(mrbc_vm *vm, mrbc_value v[], int argc) { char p[1024]; host_path(p, &v[1]); unlink(p); SET_NIL_RETURN(); }
static void c_rename(mrbc_vm *vm, mrbc_value v[], int argc) {
  char a[1024], b[1024]; host_path(a, &v[1]); host_path(b, &v[2]); rename(a, b); SET_NIL_RETURN();
}
static void c_list(mrbc_vm *vm, mrbc_value v[], int argc) {
  char p[1024]; host_path(p, &v[1]);
  mrbc_value a = mrbc_array_new(vm, 0);
  DIR *d = opendir(p);
  if (d) {
    struct dirent *e;
    while ((e = readdir(d))) {
      if (e->d_name[0] == '.') continue;
      mrbc_value s = mrbc_string_new_cstr(vm, e->d_name);
      mrbc_array_push(&a, &s);
    }
    closedir(d);
  }
  SET_RETURN(a);
}
// the free space now, and the largest piece of it: the low-water mark is kept
static void stat_now(int *free_b, int *frag) {
  struct MRBC_ALLOC_STATISTICS s; mrbc_alloc_statistics(&s);
  *free_b = s.free; *frag = s.fragmentation;
}
static void c_key(mrbc_vm *vm, mrbc_value v[], int argc) {
  int fr, fg; stat_now(&fr, &fg);
  if (fr < min_free) min_free = fr;
  while (at_key < n_keys && strcmp(keys[at_key], "WAIT") == 0) at_key++;
  if (at_key >= n_keys) {
    printf("@@DONE keys=%d free=%d frag=%d min_free=%d\n", at_key, fr, fg, min_free);
    exit(0);
  }
  const char *k = keys[at_key++];
  if (getenv("ARENA_TRACE")) printf("@@KEY %s free=%d frag=%d\n", k, fr, fg);
  if (strcmp(k, "SPACE") == 0) k = " ";
  else if (strcmp(k, "TAB") == 0) k = "\t";
  mrbc_value s = mrbc_string_new_cstr(vm, k);
  SET_RETURN(s);
}
static void c_note(mrbc_vm *vm, mrbc_value v[], int argc) {
  int fr, fg; stat_now(&fr, &fg);
  if (fr < min_free) min_free = fr;
  if (getenv("ARENA_TRACE")) printf("@@NOTE %.*s free=%d frag=%d\n", mrbc_string_size(&v[1]), mrbc_string_cstr(&v[1]), fr, fg);
  SET_NIL_RETURN();
}

int main(int argc, char **argv) {
  if (argc < 5) { fprintf(stderr, "arena <bytes> <root> <keys> <file.mrb>...\n"); return 2; }
  int size = atoi(argv[1]); root = argv[2];
  FILE *kf = fopen(argv[3], "r"); static char kb[1 << 20]; size_t kn = fread(kb, 1, sizeof kb - 1, kf); kb[kn] = 0; fclose(kf);
  keys = malloc(sizeof(char *) * 100000);
  for (char *t = strtok(kb, " \n"); t; t = strtok(NULL, " \n")) keys[n_keys++] = t;
  pool = aligned_alloc(8, size);
  mrbc_init(pool, size);
  mrbc_class *h = mrbc_define_class(0, "HostFS", mrbc_class_object);
  mrbc_define_method(0, h, "read", c_read); mrbc_define_method(0, h, "write", c_write);
  mrbc_define_method(0, h, "kind", c_kind); mrbc_define_method(0, h, "mkdir", c_mkdir);
  mrbc_define_method(0, h, "unlink", c_unlink); mrbc_define_method(0, h, "rename", c_rename);
  mrbc_define_method(0, h, "list", c_list); mrbc_define_method(0, h, "key", c_key);
  mrbc_define_method(0, h, "note", c_note);
  mrbc_vm *vm = mrbc_vm_open(NULL);
  extern void mrbc_metaprog_init(mrbc_vm *); mrbc_metaprog_init(0);
  for (int i = 4; i < argc; i++) {
    FILE *f = fopen(argv[i], "rb"); fseek(f, 0, SEEK_END); long n = ftell(f); fseek(f, 0, SEEK_SET);
    uint8_t *b = mrbc_raw_alloc(n + 1);            // kept, as the sandbox keeps it
    if (!b) arena_oom();
    fread(b, 1, n, f); fclose(f);
    if (mrbc_load_mrb(vm, b) != 0) { printf("@@LOAD_ERROR %s\n", argv[i]); return 1; }
    mrbc_vm_begin(vm);
    mrbc_vm_run(vm);
    if (mrbc_israised(vm)) { printf("@@RUNTIME_ERROR %s\n", argv[i]); mrbc_print_vm_exception(vm); return 1; }
    mrbc_vm_end(vm);
  }
  printf("@@EXIT ran off the end\n");
  return 0;
}
