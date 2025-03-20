<script lang="ts">
    import type { Snippet } from "svelte";

    let { title, children }: { title: string, children: Snippet } = $props();
</script>



<div class="section-container">
    <h1>{title}</h1>
    <div class="container">
        {@render children()}
    </div>
</div>



<style>
    .section-container {
        margin-top: var(--s16);
    }
    h1 {
        font-size: var(--s24);
    }
</style>