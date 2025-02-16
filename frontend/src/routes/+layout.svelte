<script lang="ts">
    import './reset.css';
    import './base.css';
    import NavButton from './NavButton.svelte';
</script>



<div class="navbar">
    <div class="centered-content">
        <ol class="navbar-items-separator">
            <li class="logo">
                MemoryWare
            </li>
            <li class="navbar-pages">
                <NavButton name="Final Check" url="fc"/>
                <NavButton name="Correct Media" url="corr"/>
                <NavButton name="Other Tools" url="other"/>
            </li>
        </ol>
    </div>
</div>
<div class="navbar-lower-line"></div>
<div class="below-navbar centered-content">
    <slot />
</div>



<style>
    :root {
        background-color: var(--clr-background);
        --navbar-height: 64px;
        --centered-content-size: max(66%, 500px);
        color: var(--clr-primary);
    }
    .logo {
        color: var(--clr-primary);
        font-size: 20px;
        font-style: bold;
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