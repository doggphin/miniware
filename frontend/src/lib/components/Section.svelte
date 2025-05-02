<script lang="ts">
    import type { Snippet } from "svelte";
    import Button from "$lib/components/Button.svelte";
    import Modal from "$lib/components/Modal.svelte";

    let showHelp = $state(false);
    let { title, helpContent, children }: { title: string, helpContent: Snippet, children: Snippet } = $props();
</script>



<div class="section-container">
    <div class="title">
        <h1>{title}</h1>
        {#if helpContent != undefined}
            <Button onClick={() => {showHelp = true; }} text="?"/>
            <Modal bind:showModal={showHelp}>
                {#snippet header()}
                    <h2>{title}</h2>
                {/snippet}
                {@render helpContent()}
            </Modal>
        {/if}
    </div>
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
    .title {
        display: flex;
        height: var(--s24);
        text-align: center;
        vertical-align: middle;
        gap: var(--s12);
    }
</style>
