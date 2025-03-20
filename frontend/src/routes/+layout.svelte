<script lang="ts">
    import './reset.css';
    import './base.css';
    import type { Snippet } from 'svelte';

    const navigationButtons = [
        ["Final Check", "fc"],
        ["Correct Media", "corr"],
        ["Other Tools", "other"]
    ];

    let { children } : { children : Snippet } = $props();
</script>


{#snippet navButton(name : string, url : string)}
    <a href={`/${url}`} class="noselect styled-button">
        {name}
    </a>
{/snippet}
<div class="navbar">
    <div class="centered-content">
        <ol class="navbar-items-separator">
            <li class="logo noselect">
                MemoryWare
            </li>
            <li class="navbar-pages">
                {#each navigationButtons as navigationButton}
                    {@render navButton(navigationButton[0], navigationButton[1])}
                {/each}
            </li>
        </ol>
    </div>
</div>
<div class="navbar-lower-line"></div>
<div class="below-navbar centered-content">
    {@render children()}
</div>



<style>
    :root {
        background-color: var(--clr-background);
        --navbar-height: 80px;
        color: var(--clr-primary);
    }
    .logo {
        color: var(--clr-primary);
        font-size: 20px;
        font-style: bold;
    }
    .navbar-pages {
        display: flex;
        flex-direction: row;
        gap: var(--s8);
        margin-top: var(--s8);
    }
    .navbar {
        align-content: center;
        position: absolute;
        width: 100%;
        height: var(--navbar-height);
        top: 0;
    }
    .navbar-lower-line {
        background-image: linear-gradient(to right, var(--clr-background), var(--clr-accent), var(--clr-background));
        margin-top: var(--navbar-height);
        height: var(--s4);
    }
    .centered-content {
        position: relative;
        margin: 0 auto;
        width: var(--centered-content-size);
    }
</style>