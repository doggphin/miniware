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
        padding: var(--s8);
        margin-top: var(--s8);
        border-radius: var(--s8);
    }
    .container {
        padding: var(--s8);
    }
    h1 {
        font-size: var(--s24);
    }
</style>