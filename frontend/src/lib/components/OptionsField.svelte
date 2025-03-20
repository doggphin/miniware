<script lang="ts">
    import TitledComponent from "./TitledComponent.svelte";

    interface Props {
        title : string
        options : Array<any>
        unselectedText : any
        optionState : any
    }

    let { title, options, unselectedText, optionState: optionState = $bindable() } : Props = $props();
</script>


<TitledComponent title={title}>
    <select bind:value={optionState}>
        <option value="" selected disabled hidden> {unselectedText} </option>
        {#each options as option}
            <option value={option}>{option}</option>
        {/each}
    </select>
</TitledComponent>