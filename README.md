# TicketOrLeaveIt Server

TicketOrLeaveIt Server is a backend service for managing events, tickets, and user invitations. It is built with FastAPI, SQLModel, and other modern technologies.

## Features

- **User Management**: Create, update, and manage users and their roles within organizations.
- **Organization Management**: Create and manage organizations, including adding members and assigning roles.
- **Event Management**: Schedule events, manage tickets, and handle reservations.
- **Invitation System**: Send and manage invitations to join organizations.
- **Email Notifications**: Send email notifications for various events such as ticket confirmations and invitations.

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL (for production) or SQLite (for development)
- FastAPI
- SQLModel
- Uvicorn (ASGI server)

### Installation

1. Clone the repository:
   git clone https://github.com/TicketOrLeave/Server.git

2. Navigate to the project directory:
   cd /Server

3. Install the required Python packages:
   pip install -r requirements.txt

4. Set up the environment variables by copying the `.env.example` file to `.env` and filling in the required values.

### Running the Server

To run the server in development mode, use the following command:

uvicorn app.main:api --reload

This will start the server on `http://localhost:8000`.

## Contributing

Contributions are welcome!

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or concerns, please open an issue on the GitHub repository.
