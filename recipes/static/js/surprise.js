(() => {
    const page = document.querySelector('.surprise-page');
    let loading = false;

    page.addEventListener('submit', async (event) => {
        if (event.target.id !== 'surpriseForm') return;
        event.preventDefault();
        if (loading) return;
        loading = true;
        const form = event.target;
        const button = form.querySelector('button');
        button.disabled = true;
        page.querySelector('.surprise-error')?.remove();
        const url = new URL(form.action, window.location.href);
        url.search = new URLSearchParams(new FormData(form)).toString();
        try {
            const response = await fetch(url, {cache: 'no-store'});
            if (!response.ok) throw new Error('Recipe request failed');
            const html = new DOMParser().parseFromString(await response.text(), 'text/html');
            const nextPage = html.querySelector('.surprise-page');
            if (!nextPage) throw new Error('Recipe page is missing');
            // Keep the current viewport and enough document height, including near the footer.
            const scrollX = window.scrollX;
            const scrollY = window.scrollY;
            page.style.minHeight = `${page.getBoundingClientRect().height}px`;
            page.replaceChildren(...nextPage.childNodes);
            animate();
            window.scrollTo({left: scrollX, top: scrollY, behavior: 'instant'});
        } catch (error) {
            button.disabled = false;
            const message = document.createElement('p');
            message.className = 'surprise-error';
            message.setAttribute('role', 'alert');
            message.textContent = 'We couldn’t choose a recipe. Please try again.';
            page.appendChild(message);
        } finally {
            loading = false;
        }
    });

    function animate() {
        if (!document.getElementById('surpriseResult')) return;
        const result = document.getElementById('surpriseResult');
        const shuffle = document.getElementById('surpriseShuffle');
        const button = document.getElementById('surpriseButton');
        const status = document.getElementById('surpriseStatus');
        const confetti = document.getElementById('surpriseConfetti');
        const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
        const recipes = JSON.parse(document.getElementById('surpriseRecipes').textContent);
        const image = document.getElementById('shuffleImage');
        const name = document.getElementById('shuffleName');
        let timer;
        let finished = false;

        // Preload the small sample while keeping Django's selected card intact.
        recipes.forEach(recipe => {
            if (recipe.image) new Image().src = recipe.image;
        });
        image.addEventListener('error', () => { image.hidden = true; });
        result.querySelectorAll('.recipe-image img').forEach(img => {
            const fallback = () => {
                const placeholder = document.createElement('div');
                placeholder.className = 'image-placeholder';
                placeholder.textContent = '🍽️';
                img.replaceWith(placeholder);
            };
            img.addEventListener('error', fallback, {once: true});
            if (img.complete && !img.naturalWidth) fallback();
        });

        function reveal() {
            if (finished) return;
            finished = true;
            clearTimeout(timer);
            shuffle.hidden = true;
            result.hidden = false;
            button.disabled = false;
            status.textContent = 'Your recipe is ready: ' + result.querySelector('h3').textContent.trim();
            if (motion.matches) {
                motion.removeEventListener('change', onMotionChange);
                return;
            }
            result.classList.add('surprise-revealed');
            for (let i = 0; i < 24; i++) {
                const piece = document.createElement('i');
                piece.style.setProperty('--x', `${Math.random() * 100}%`);
                piece.style.setProperty('--delay', `${Math.random() * 0.3}s`);
                piece.style.setProperty('--drift', `${(Math.random() - 0.5) * 120}px`);
                confetti.appendChild(piece);
            }
            setTimeout(() => {
                confetti.replaceChildren();
                motion.removeEventListener('change', onMotionChange);
            }, 1900);
        }

        const onMotionChange = () => {
            if (motion.matches) {
                reveal();
                confetti.replaceChildren();
            }
        };
        motion.addEventListener('change', onMotionChange);
        if (motion.matches || !recipes.length) {
            reveal();
            return;
        }
        shuffle.style.minHeight = `${result.getBoundingClientRect().height}px`;
        result.hidden = true;
        shuffle.hidden = false;
        button.disabled = true;
        status.textContent = 'Shuffling recipes…';
        const delays = [70, 80, 90, 100, 120, 140, 170, 210, 260, 330, 400, 480];
        let frame = 0;
        function tick() {
            const recipe = recipes[frame % recipes.length];
            name.textContent = recipe.name;
            image.hidden = !recipe.image;
            if (recipe.image) image.src = recipe.image;
            else image.removeAttribute('src');
            timer = setTimeout(++frame < delays.length ? tick : reveal, delays[frame - 1]);
        }
        tick();
    }

    animate();
})();
