<script lang="ts">
    interface Props {
        text: string,
        onClick : Function
    };

    let { text, onClick } : Props = $props();
</script>


<button class="styled-button clickable" onclick={() => {onClick()}}>
    {text}
</button>