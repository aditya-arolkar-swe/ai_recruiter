document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('candidate-details');
    const closeBtn = document.getElementsByClassName('close')[0];
    const candidateNames = document.getElementsByClassName('candidate-name');
    const inviteBtns = document.getElementsByClassName('invite-btn');
    const modalInviteBtn = document.getElementById('modal-invite-btn');

    Array.from(candidateNames).forEach(name => {
        name.addEventListener('click', function(e) {
            e.preventDefault();
            const candidateId = this.getAttribute('data-id');
            fetch(`/candidate/${candidateId}`)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('modal-name').textContent = data.name;
                    document.getElementById('modal-position').textContent = data.position;
                    document.getElementById('modal-email').textContent = data.email;
                    document.getElementById('modal-resume').textContent = data.resume;
                    modalInviteBtn.setAttribute('data-id', candidateId);
                    modal.style.display = 'block';
                });
        });
    });

    closeBtn.onclick = () => {
        modal.style.display = 'none';
    };

    window.onclick = (event) => {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    };

    Array.from(inviteBtns).forEach(btn => {
        btn.addEventListener('click', sendInvite);
    });

    modalInviteBtn.addEventListener('click', sendInvite);

    function sendInvite() {
        const candidateId = this.getAttribute('data-id');
        fetch(`/invite/${candidateId}`)
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                modal.style.display = 'none';
            });
    }
});