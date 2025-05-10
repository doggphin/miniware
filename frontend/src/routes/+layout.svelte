<script lang="ts">
    import './reset.css';
    import './base.css';
    import type { Snippet } from 'svelte';

    const navigationButtons = [
        ["Correct Media", "corr"],
        ["Other Tools", "other"],
        //["Sheets FC (WIP)", "fc"],
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
                MiniWare
            </li>
            <li class="navbar-pages">
                {#each navigationButtons as navigationButton}
                    {@render navButton(navigationButton[0], navigationButton[1])}
                {/each}
            </li>
        </ol>
    </div>
</div>

<div class="navbar-lower-line top-navbar-spacer"></div>

<div class="below-navbar centered-content">
    {@render children()}
</div>

<div class="footer-spacer"></div>

<div class="footer">
    <div class="navbar-lower-line"></div>
    <div class="footer-container">
        Made by Brendan Lancaster (2025). 
        Need help? 
        E-mail me at <a style="margin: 0 0 0 var(--s8);" href="mailto:brendan.howard.lancaster@gmail.com"> brendan.howard.lancaster@gmail.com</a>!
    </div>
</div>



<style>
    :root {
        background-color: var(--clr-background);
        --navbar-height: 80px;
        color: var(--clr-primary);
    }
    .footer-spacer {
        margin-bottom: 60px;
    }
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 1;
        background-color: var(--clr-background);
    }
    .footer-container {
        display: flex;
        justify-content: center;
        padding: var(--s8);
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
        height: var(--s4);
    }
    .top-navbar-spacer {
        margin-top: var(--navbar-height);
    }
    .centered-content {
        position: relative;
        margin: 0 auto;
        width: var(--centered-content-size);
    }
</style>