/*
 * Multithreaded DAXPY benchmark for gem5.
 * Operation: y[i] = a * x[i] + y[i]
 *
 * Usage: ./daxpy_mt <number_of_elements> <number_of_threads>
 */

#define _POSIX_C_SOURCE 200809L

#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#include <sys/time.h>

typedef struct {
    size_t start;
    size_t end;
    double a;
    const double *x;
    double *y;
} worker_arg_t;

/* Each worker computes its assigned section of the vectors. */
void *daxpy_worker(void *arg)
{
    worker_arg_t *w = (worker_arg_t *)arg;

    for (size_t i = w->start; i < w->end; i++) {
        w->y[i] = w->a * w->x[i] + w->y[i];
    }

    return NULL;
}

int main(int argc, char **argv)
{
    if (argc != 3) {
        printf("Usage: %s <vector_size> <threads>\n", argv[0]);
        return 1;
    }

    size_t n = (size_t)strtoull(argv[1], NULL, 10);
    int num_threads = atoi(argv[2]);

    if (n == 0 || num_threads < 1) {
        printf("Invalid vector size or thread count.\n");
        return 1;
    }

    double a = 2.5;

    double *x = malloc(n * sizeof(double));
    double *y = malloc(n * sizeof(double));

    pthread_t *threads =
        malloc(num_threads * sizeof(pthread_t));

    worker_arg_t *args =
        malloc(num_threads * sizeof(worker_arg_t));

    if (!x || !y || !threads || !args) {
        printf("Memory allocation failed.\n");
        free(x);
        free(y);
        free(threads);
        free(args);
        return 1;
    }

    /* Initialize the input vectors. */
    for (size_t i = 0; i < n; i++) {
        x[i] = 1.0 + (double)i * 0.001;
        y[i] = 2.0;
    }

    struct timeval start, end;
    gettimeofday(&start, NULL);

    /* Divide the vector into approximately equal sections. */
    for (int t = 0; t < num_threads; t++) {

        args[t].start = (n * t) / num_threads;
        args[t].end = (n * (t + 1)) / num_threads;

        args[t].a = a;
        args[t].x = x;
        args[t].y = y;

        int rc = pthread_create(
            &threads[t],
            NULL,
            daxpy_worker,
            &args[t]
        );

        if (rc != 0) {
            printf("Thread creation failed: %d\n", rc);
            return 1;
        }
    }

    /* Wait for every worker to finish. */
    for (int t = 0; t < num_threads; t++) {
        pthread_join(threads[t], NULL);
    }

    gettimeofday(&end, NULL);

    /* Calculate checksum to verify the result. */
    double checksum = 0.0;

    for (size_t i = 0; i < n; i++) {
        checksum += y[i];
    }

    double elapsed =
        (end.tv_sec - start.tv_sec) +
        (end.tv_usec - start.tv_usec) / 1000000.0;

    printf("\n========================================\n");
    printf("       MULTITHREADED DAXPY RESULT\n");
    printf("========================================\n");

    printf("Vector size : %zu\n", n);
    printf("Threads     : %d\n", num_threads);
    printf("Scalar a    : %.2f\n", a);
    printf("First y     : %.6f\n", y[0]);
    printf("Checksum    : %.12f\n", checksum);
    printf("Time        : %.6f seconds\n", elapsed);

    printf("========================================\n");

    free(x);
    free(y);
    free(threads);
    free(args);

    return 0;
}
