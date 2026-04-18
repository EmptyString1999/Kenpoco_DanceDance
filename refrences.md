# References

https://github.com/ccgargantua/arena-allocator/blob/main/arena.h

``` C
Arena* arena_create(size_t size)
{
    Arena *arena;
    void *region;

    if (size == 0)
    {
        return NULL;
    }

    /* A malloc of 0 is implementation defined, so the above check is necessary */
    arena = ARENA_MALLOC(sizeof(Arena));
    if (arena == NULL)
    {
        return NULL;
    }

    region = ARENA_MALLOC(size);
    if (region == NULL)
    {
        return NULL;
    }

    arena_init(arena, region, size);

    return arena;
}

void arena_init(Arena *arena, void *region, size_t size)
{
    if (!arena)
    {
        return;
    }
    
    if ((region == NULL) ^ (size == 0))
    {
        return;
    }

    arena->region = region;
    arena->index = 0;
    arena->size = size;

    #ifdef ARENA_DEBUG
    arena->head_allocation = NULL;
    arena->allocations = 0;
    #endif /* ARENA_DEBUG */
}

void* arena_alloc(Arena *arena, size_t size)
{
    return arena_alloc_aligned(arena, size, ARENA_DEFAULT_ALIGNMENT);
}



void* arena_alloc_aligned(Arena *arena, size_t size, unsigned int alignment)
{
    unsigned int offset;

    if (size == 0)
    {
        return NULL;
    }

    if (arena == NULL || arena->region == NULL)
    {
        return NULL;
    }

    if (alignment != 0)
    {
        offset = (size_t)(arena->region + arena->index) % alignment;
        if (offset > 0)
        {
            arena->index = arena->index - offset + alignment;
        }
    }
    else
    {
        offset = 0;
    }

    if (arena->size - arena->index < size)
    {
        return NULL;
    }

    #ifdef ARENA_DEBUG
    arena_add_allocation(arena, size);
    #endif /* ARENA_DEBUG */

    arena->index += size;
    return arena->region + (arena->index - size);
}



size_t arena_copy(Arena *dest, Arena *src)
{
    size_t bytes;

    if (dest == NULL || src == NULL)
    {
        return 0;
    }

    if (src->index < dest->size)
    {
        bytes = src->index;
    }
    else
    {
        bytes = dest->size;
    }

    ARENA_MEMCPY(dest->region, src->region, bytes);
    dest->index = bytes;

    return bytes;
}



void arena_clear(Arena *arena)
{
    if (arena == NULL)
    {
        return;
    }

    arena->index = 0;

    #ifdef ARENA_DEBUG
    arena_delete_allocation_list(arena);
    #endif /* ARENA_DEBUG */
}



void arena_destroy(Arena *arena)
{
    if (arena == NULL)
    {
        return;
    }

    #ifdef ARENA_DEBUG
    arena_delete_allocation_list(arena);
    #endif /* ARENA_DEBUG */

    if (arena->region != NULL)
    {
        ARENA_FREE(arena->region);
    }

    ARENA_FREE(arena);
}



#ifdef ARENA_DEBUG



Arena_Allocation* arena_get_allocation_struct(Arena *arena, void *ptr)
{
    Arena_Allocation *current;

    if (arena == NULL || ptr == NULL)
    {
        return NULL;
    }

    current = arena->head_allocation;
    while (current != NULL)
    {
        if (current->pointer == (char *)ptr)
        {
            return current;
        }
        current = current->next;
    }

    return NULL;
}



void arena_add_allocation(Arena *arena, size_t size)
{
    if (arena == NULL)
    {
        return;
    }

    if (arena->head_allocation == NULL)
    {
        arena->head_allocation = malloc(sizeof(Arena_Allocation));
        arena->head_allocation->index = arena->index;
        arena->head_allocation->size = size;
        arena->head_allocation->pointer = arena->region + arena->index;
        arena->head_allocation->next = NULL;
    }
    else
    {
        Arena_Allocation *current = arena->head_allocation;
        while (current->next != NULL)
        {
            current = current->next;
        }

        current->next = malloc(sizeof(Arena_Allocation));
        current->next->index = arena->index;
        current->next->size = size;
        current->next->pointer = arena->region + arena->index;
        current->next->next = NULL;
    }

    arena->allocations++;
}



void arena_delete_allocation_list(Arena *arena)
{
    if (arena == NULL)
    {
        return;
    }

    while (arena->head_allocation != NULL)
    {
        Arena_Allocation *next = arena->head_allocation->next;
        free(arena->head_allocation);
        arena->head_allocation = next;
    }

    arena->allocations = 0;
    arena->head_allocation = NULL;
}



#endif /* ARENA_DEBUG */
```
```
```
